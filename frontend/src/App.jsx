import { useCallback, useEffect, useState } from 'react';
import { api } from './api.js';

// the item types and the names people see for them
const CATEGORIES = {
  ELECTRONICS: 'Electronics',
  BOOKS: 'Books & notes',
  ID_CARD: 'ID card',
  CLOTHING: 'Clothing',
  KEYS: 'Keys',
  BOTTLE: 'Bottle',
  OTHER: 'Other',
};

// the filter buttons above the board
const FILTERS = [
  { value: '', label: 'Everything' },
  { value: 'LOST', label: 'Lost' },
  { value: 'FOUND', label: 'Found' },
  { value: 'CLAIMED', label: 'Back with owner' },
];

// the word printed on the stamp of each tag
const STAMP = { LOST: 'Lost', FOUND: 'Found', CLAIMED: 'Claimed' };

// a blank form for a new report
const EMPTY_FORM = {
  title: '', description: '', category: 'OTHER', status: 'LOST', location: '', reporter_name: '', contact: '',
};

// turn a date into short text like 5 min ago
function timeAgo(iso) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

// the pop up form used to add a new report or edit one
function ItemForm({ initial, onCancel, onSave }) {
  const [form, setForm] = useState(initial);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const editing = Boolean(initial.id);
  // update one field of the form when the user types
  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });

  // send the form and show an error if saving fails
  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await onSave(form);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="overlay" role="presentation" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <form className="sheet" onSubmit={submit} aria-labelledby="sheet-title">
        <h2 id="sheet-title">{editing ? 'Edit this report' : form.status === 'FOUND' ? 'Report something you found' : 'Report something you lost'}</h2>

        {/* the lost or found choice is only shown for a new report */}
        {!editing && (
          <div className="choice" role="radiogroup" aria-label="What happened">
            {['LOST', 'FOUND'].map((value) => (
              <label key={value} className={form.status === value ? 'on' : ''}>
                <input type="radio" name="status" value={value} checked={form.status === value} onChange={set('status')} />
                {value === 'LOST' ? 'I lost it' : 'I found it'}
              </label>
            ))}
          </div>
        )}

        <label className="field">
          <span>What is it?</span>
          <input required minLength={2} value={form.title} onChange={set('title')} placeholder="Grey Casio calculator" />
        </label>
        <div className="row">
          <label className="field">
            <span>Type</span>
            <select value={form.category} onChange={set('category')}>
              {Object.entries(CATEGORIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Where on campus?</span>
            <input required minLength={2} value={form.location} onChange={set('location')} placeholder="Block C, room 204" />
          </label>
        </div>
        <label className="field">
          <span>Details that help the owner recognise it</span>
          <textarea rows={3} value={form.description} onChange={set('description')} placeholder="Name written inside the cover, blue sticker on the back" />
        </label>
        <div className="row">
          <label className="field">
            <span>Your name</span>
            <input required minLength={2} value={form.reporter_name} onChange={set('reporter_name')} />
          </label>
          <label className="field">
            <span>Phone or email</span>
            <input required minLength={3} value={form.contact} onChange={set('contact')} />
          </label>
        </div>

        {error && <p className="form-error" role="alert">Could not save: {error}</p>}
        <div className="actions">
          <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
          <button type="submit" className="primary" disabled={saving}>{saving ? 'Saving…' : editing ? 'Save changes' : 'Post report'}</button>
        </div>
      </form>
    </div>
  );
}

// one item on the board drawn as a paper tag
function Tag({ item, onEdit, onClaim, onDelete }) {
  const [claiming, setClaiming] = useState(false);
  const [name, setName] = useState('');

  return (
    <article className={`tag tag-${item.status.toLowerCase()}`}>
      <span className="hole" aria-hidden="true" />
      <span className="stamp">{STAMP[item.status]}</span>
      <h3>{item.title}</h3>
      <p className="where">{item.location}</p>
      {item.description && <p className="desc">{item.description}</p>}
      <dl>
        <div><dt>Type</dt><dd>{CATEGORIES[item.category]}</dd></div>
        <div><dt>Posted</dt><dd>{timeAgo(item.reported_at)} by {item.reporter_name}</dd></div>
        <div><dt>Contact</dt><dd>{item.contact}</dd></div>
        {item.claimed_by && <div><dt>Picked up by</dt><dd>{item.claimed_by}</dd></div>}
      </dl>

      {/* show the small claim form or the normal buttons */}
      {claiming ? (
        <form className="claim" onSubmit={(e) => { e.preventDefault(); onClaim(item, name); }}>
          <input autoFocus required minLength={2} value={name} onChange={(e) => setName(e.target.value)} placeholder="Name of the owner" aria-label="Name of the owner" />
          <button className="primary small" type="submit">Mark returned</button>
          <button className="ghost small" type="button" onClick={() => setClaiming(false)}>Cancel</button>
        </form>
      ) : (
        <div className="tag-actions">
          {item.status !== 'CLAIMED' && <button className="primary small" onClick={() => setClaiming(true)}>Mark returned</button>}
          <button className="ghost small" onClick={() => onEdit(item)}>Edit</button>
          <button className="ghost small danger" onClick={() => onDelete(item)}>Remove</button>
        </div>
      )}
    </article>
  );
}

// the main page
export default function App() {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(null);
  const [notice, setNotice] = useState('');

  // get the items and the counts from the api
  const load = useCallback(async () => {
    try {
      const params = {};
      if (status) params.status = status;
      if (query.trim()) params.q = query.trim();
      const [list, counts] = await Promise.all([api.list(params), api.stats()]);
      setItems(list);
      setStats(counts);
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [status, query]);

  // wait a little after typing before loading so we do not call the api on every key
  useEffect(() => {
    const timer = setTimeout(load, 200);
    return () => clearTimeout(timer);
  }, [load]);

  // hide the notice message after a few seconds
  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(''), 3500);
    return () => clearTimeout(timer);
  }, [notice]);

  // save a new report or the changes to an old one
  async function save(form) {
    if (form.id) {
      const { id, title, description, category, location, reporter_name, contact } = form;
      await api.update(id, { title, description, category, location, reporter_name, contact });
      setNotice('Changes saved.');
    } else {
      await api.create(form);
      setNotice(form.status === 'FOUND' ? 'Report posted. Thanks for handing it in.' : 'Report posted. We hope it turns up soon.');
    }
    setEditing(null);
    load();
  }

  // mark an item as given back to its owner
  async function claim(item, name) {
    try {
      await api.claim(item.id, name);
      setNotice(`"${item.title}" marked returned to ${name}.`);
      load();
    } catch (err) {
      setNotice(`Could not mark returned: ${err.message}`);
    }
  }

  // ask first and then remove an item from the board
  async function remove(item) {
    if (!window.confirm(`Remove "${item.title}" from the board?`)) return;
    try {
      await api.remove(item.id);
      setNotice(`"${item.title}" removed.`);
      load();
    } catch (err) {
      setNotice(`Could not remove: ${err.message}`);
    }
  }

  return (
    <div className="page">
      <header className="masthead">
        <p className="brand">Campus Lost &amp; Found</p>
        <h1>Lost something on campus?</h1>
        <p className="lede">Search the board before you report. Someone may have handed it in already.</p>
        <label className="search">
          <span className="sr-only">Search items</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try “calculator”, “library” or “keys”" />
        </label>
        <div className="cta">
          <button className="primary" onClick={() => setEditing({ ...EMPTY_FORM, status: 'LOST' })}>I lost something</button>
          <button className="secondary" onClick={() => setEditing({ ...EMPTY_FORM, status: 'FOUND' })}>I found something</button>
        </div>
      </header>

      <main>
        <div className="toolbar">
          <div className="filters" role="tablist" aria-label="Filter by status">
            {FILTERS.map((f) => (
              <button key={f.value} role="tab" aria-selected={status === f.value} className={status === f.value ? 'on' : ''} onClick={() => setStatus(f.value)}>
                {f.label}
                {stats && <span className="count">{f.value ? stats[f.value.toLowerCase()] : stats.total}</span>}
              </button>
            ))}
          </div>
          {stats && stats.total > 0 && (
            <p className="tally">{stats.claimed} of {stats.total} items are back with their owners.</p>
          )}
        </div>

        {/* loading and error and empty messages */}
        {loading && <p className="state">Loading the board…</p>}
        {!loading && error && (
          <div className="state error" role="alert">
            <p><strong>The board can't reach the server.</strong> {error}</p>
            <p>Check that the backend is running, then <button className="link" onClick={load}>try again</button>.</p>
          </div>
        )}
        {!loading && !error && items.length === 0 && (
          <div className="state">
            <p><strong>{query || status ? 'Nothing matches that yet.' : 'The board is empty.'}</strong></p>
            <p>Post the first report so others know what to look out for.</p>
          </div>
        )}

        {/* the board with one tag for each item */}
        <section className="board" aria-live="polite">
          {items.map((item) => (
            <Tag key={item.id} item={item} onEdit={setEditing} onClaim={claim} onDelete={remove} />
          ))}
        </section>
      </main>

      <footer>
        Hand found items to the security desk at the main gate. Posting here helps the owner know where to go.
      </footer>

      {editing && <ItemForm initial={editing} onCancel={() => setEditing(null)} onSave={save} />}
      {notice && <div className="toast" role="status">{notice}</div>}
    </div>
  );
}
