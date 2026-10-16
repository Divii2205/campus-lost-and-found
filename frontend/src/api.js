// The browser only talks to /api on its own origin.
// nginx (Docker Compose) or the Ingress (Kubernetes) routes it to the backend.
const BASE = '/api/items';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join(', ') : body.detail;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  list: (params) => request(`?${new URLSearchParams(params)}`),
  stats: () => request('/stats'),
  create: (item) => request('', { method: 'POST', body: JSON.stringify(item) }),
  update: (id, item) => request(`/${id}`, { method: 'PUT', body: JSON.stringify(item) }),
  claim: (id, claimedBy) => request(`/${id}/claim`, { method: 'PATCH', body: JSON.stringify({ claimed_by: claimedBy }) }),
  remove: (id) => request(`/${id}`, { method: 'DELETE' }),
};
