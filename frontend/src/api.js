// the browser only calls the api path on its own website address
// nginx in docker compose or the ingress in kubernetes sends it on to the backend
const BASE = '/api/items';

// send a request to the api and turn the answer into data
async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  // if something went wrong show the error message from the api
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join(', ') : body.detail;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  // a 204 answer has no body so return nothing
  return response.status === 204 ? null : response.json();
}

// one simple function for each api action
export const api = {
  list: (params) => request(`?${new URLSearchParams(params)}`),
  stats: () => request('/stats'),
  create: (item) => request('', { method: 'POST', body: JSON.stringify(item) }),
  update: (id, item) => request(`/${id}`, { method: 'PUT', body: JSON.stringify(item) }),
  claim: (id, claimedBy) => request(`/${id}/claim`, { method: 'PATCH', body: JSON.stringify({ claimed_by: claimedBy }) }),
  remove: (id) => request(`/${id}`, { method: 'DELETE' }),
};
