export function useApiError() {
  async function safeFetch(url, options = {}) {
    const res = await fetch(url, options);
    if (res.status === 422) throw new Error('Invalid request format sent to server.');
    if (res.status === 401) throw new Error('Session expired. Please log in again.');
    if (res.status === 500) throw new Error('Server error. Check backend logs.');
    if (!res.ok) throw new Error(`Request failed with status ${res.status}`);
    return res.json();
  }
  return { safeFetch };
}