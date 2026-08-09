import httpx
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import StructuredTool

def create_pydantic_model_for_tool(tool_name: str, parameters: List[Dict[str, Any]]):
    fields = {}
    for p in parameters:
        p_name = p.get("name")
        if not p_name:
            continue
        p_desc = p.get("description", "")
        p_type_str = p.get("type", "string")
        p_required = p.get("required", False)
        
        # map type string to python type
        if p_type_str == "number":
            p_type = float
        elif p_type_str == "boolean":
            p_type = bool
        else:
            p_type = str
            
        if p_required:
            fields[p_name] = (p_type, Field(description=p_desc))
        else:
            fields[p_name] = (Optional[p_type], Field(default=None, description=p_desc))
            
    if not fields:
        # Dummy field if there are no parameters
        fields["dummy"] = (Optional[str], Field(default=None, description="Dummy argument"))

    return create_model(f"{tool_name}_args", **fields)

def build_langchain_tool(agent_tool, websocket):
    args_schema = create_pydantic_model_for_tool(agent_tool.name, agent_tool.parameters)
    
    async def _run_tool(**kwargs):
        # Remove dummy field if present
        kwargs.pop("dummy", None)
        
        start_time = time.time()
        try:
            await websocket.send_json({
                "type": "tool_call",
                "status": "in_progress",
                "tool_name": agent_tool.name,
                "arguments": kwargs
            })
        except Exception:
            pass

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(agent_tool.webhook_url, json=kwargs, timeout=10.0)
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    try:
                        await websocket.send_json({
                            "type": "tool_call",
                            "status": "success",
                            "tool_name": agent_tool.name,
                            "latency_ms": latency_ms,
                            "response": response.text
                        })
                    except Exception:
                        pass
                    return response.text
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        await websocket.send_json({
                            "type": "tool_call",
                            "status": "error",
                            "tool_name": agent_tool.name,
                            "error": error_msg
                        })
                    except Exception:
                        pass
                    return f"Tool execution failed: {error_msg}"
        except Exception as e:
            try:
                await websocket.send_json({
                    "type": "tool_call",
                    "status": "error",
                    "tool_name": agent_tool.name,
                    "error": str(e)
                })
            except Exception:
                pass
            return f"Tool execution failed: {str(e)}"

    return StructuredTool(
        name=agent_tool.name,
        description=agent_tool.description or f"Call custom webhook at {agent_tool.webhook_url}",
        func=None,
        coroutine=_run_tool,
        args_schema=args_schema
    )
