"""
Security layer for tool/webhook URL validation.

Provides SSRF protection, response size caps, and timeouts.
"""
import asyncio
import ipaddress
import socket
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from app.config import settings

TOOL_CALL_TIMEOUT_SECONDS = 10
TOOL_RESPONSE_MAX_BYTES = 8 * 1024  # 8 KB
TOOL_CALLS_PER_TURN_LIMIT = 5

# Private / link-local IP ranges that must never be reached
_PRIVATE_RANGES: List[ipaddress.IPv4Network] = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("169.254.0.0/16"),
    ipaddress.IPv4Network("127.0.0.0/8"),
]

_LOOPBACK_NAMES = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "localhost6"}

# Per-session tool call counter
_tool_call_counts: Dict[str, int] = {}


def _is_production() -> bool:
    return not getattr(settings, "debug", False)


def validate_tool_url(url: str) -> None:
    """Validate a tool URL for safety. Raises ValueError on any violation.

    Called both at tool-save time and at call-time (defense in depth).
    """
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError("URL must have a scheme and host")

    if _is_production() and parsed.scheme != "https":
        raise ValueError("Only HTTPS URLs are allowed in production")

    hostname = parsed.hostname or ""

    # Reject obviously dangerous hostnames
    if hostname.lower() in _LOOPBACK_NAMES:
        raise ValueError(f"URL hostname resolves to loopback: {hostname}")

    # Resolve hostname to IPs
    addrs = _resolve_hostname(hostname)
    for family, ip_str in addrs:
        _check_ip(ip_str)

    # Check if resolves to the backend's own address
    _check_self_reference(hostname, parsed.port or 443)


def _resolve_hostname(hostname: str) -> List[Tuple[int, str]]:
    """Resolve a hostname to a list of (family, ip_str) tuples."""
    try:
        infos = socket.getaddrinfo(hostname, None)
        results: List[Tuple[int, str]] = []
        seen = set()
        for info in infos:
            family = info[0]
            addr = info[4][0]
            if addr not in seen:
                seen.add(addr)
                results.append((family, addr))
        return results
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")


def _check_ip(ip_str: str) -> None:
    """Check if an IP address is in a private/blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return

    if ip.is_loopback:
        raise ValueError(f"Loopback address not allowed: {ip_str}")

    if isinstance(ip, ipaddress.IPv4Address):
        for net in _PRIVATE_RANGES:
            if ip in net:
                raise ValueError(f"Private IP range not allowed: {ip_str} ({net})")

    if ip.is_link_local:
        raise ValueError(f"Link-local address not allowed: {ip_str}")


def _check_self_reference(hostname: str, port: int) -> None:
    """Check if the target URL points to the backend itself."""
    try:
        own_addrs = _resolve_hostname(socket.gethostname())
        own_ip_set = {addr for _, addr in own_addrs}

        target_addrs = _resolve_hostname(hostname)
        target_ip_set = {addr for _, addr in target_addrs}

        if own_ip_set & target_ip_set:
            raise ValueError(
                f"URL resolves to the backend's own address: {hostname} resolves to "
                f"{', '.join(target_ip_set)}"
            )
        self_check_port = getattr(settings, "port", None)
        if self_check_port and port == self_check_port:
            if own_ip_set & target_ip_set:
                raise ValueError("URL points to the backend's own listening port")
    except Exception:
        pass


def get_tool_call_count(session_id: str) -> int:
    return _tool_call_counts.get(session_id, 0)


def increment_tool_call_count(session_id: str) -> int:
    count = _tool_call_counts.get(session_id, 0) + 1
    _tool_call_counts[session_id] = count
    return count


def reset_tool_call_count(session_id: str) -> None:
    _tool_call_counts.pop(session_id, None)


async def execute_tool_webhook(
    url: str,
    http_method: str,
    payload: dict,
    session_id: str,
) -> dict:
    """Execute a tool webhook call with full security checks.

    Returns a dict with keys: success (bool), content (str), status_code (int),
    latency_ms (float).
    """
    import time

    start = time.time()

    # Call-time URL validation (defense in depth — save-time check may be stale)
    validate_tool_url(url)

    # Per-turn cap
    call_count = increment_tool_call_count(session_id)
    if call_count > TOOL_CALLS_PER_TURN_LIMIT:
        return {
            "success": False,
            "content": "Tool call limit reached for this conversation turn.",
            "status_code": 0,
            "latency_ms": 0,
        }

    method = http_method.upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        return {
            "success": False,
            "content": f"Unsupported HTTP method: {method}",
            "status_code": 0,
            "latency_ms": 0,
        }

    async with httpx.AsyncClient(timeout=TOOL_CALL_TIMEOUT_SECONDS) as client:
        try:
            if method == "GET":
                resp = await client.get(url, params=payload)
            elif method == "POST":
                resp = await client.post(url, json=payload)
            elif method == "PUT":
                resp = await client.put(url, json=payload)
            elif method == "PATCH":
                resp = await client.patch(url, json=payload)
            elif method == "DELETE":
                resp = await client.delete(url, params=payload)

            latency_ms = round((time.time() - start) * 1000, 1)

            body = resp.text[:TOOL_RESPONSE_MAX_BYTES]
            return {
                "success": 200 <= resp.status_code < 300,
                "content": body,
                "status_code": resp.status_code,
                "latency_ms": latency_ms,
            }

        except httpx.TimeoutException:
            latency_ms = round((time.time() - start) * 1000, 1)
            return {
                "success": False,
                "content": "Tool webhook timed out",
                "status_code": 0,
                "latency_ms": latency_ms,
            }
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return {
                "success": False,
                "content": f"Tool webhook error: {str(e)}",
                "status_code": 0,
                "latency_ms": latency_ms,
            }
