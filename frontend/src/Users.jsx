import { useState, useEffect } from 'react'
import { Plus, Pencil, Trash2, LogOut, ShieldCheck, X, Save, Loader } from 'lucide-react'
import { listUsers, createUser, updateUser, deleteUser } from './api.js'

const ROLES = ['demo', 'free', 'paid', 'admin']
const ROLE_COLOURS = { admin: 'text-amber-400', paid: 'text-green-400', free: 'text-blue-400', demo: 'text-gray-400' }

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
          <h2 className="font-semibold text-gray-100">{title}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300"><X size={18} /></button>
        </div>
        <div className="p-5 space-y-4">{children}</div>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  )
}

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500 transition-colors"

function UserForm({ initial, onSave, onClose }) {
  const isEdit = !!initial
  const [username,    setUsername]    = useState(initial?.username    ?? '')
  const [displayName, setDisplayName] = useState(initial?.display_name ?? '')
  const [password,    setPassword]    = useState('')
  const [role,        setRole]        = useState(initial?.role        ?? 'free')
  const [isActive,    setIsActive]    = useState(initial?.is_active   ?? true)
  const [error,       setError]       = useState('')
  const [busy,        setBusy]        = useState(false)

  async function submit(e) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const body = { display_name: displayName || null, role, is_active: isActive }
      if (!isEdit) { body.username = username; body.password = password }
      else if (password) body.password = password
      await onSave(body)
      onClose()
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {!isEdit && (
        <Field label="Username">
          <input className={inp} value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
        </Field>
      )}
      <Field label="Display name (optional)">
        <input className={inp} value={displayName} onChange={e => setDisplayName(e.target.value)} placeholder={initial?.username ?? 'Same as username'} />
      </Field>
      <Field label={isEdit ? 'New password (leave blank to keep)' : 'Password'}>
        <input type="password" className={inp} value={password} onChange={e => setPassword(e.target.value)} required={!isEdit} />
      </Field>
      <Field label="Role">
        <select className={inp} value={role} onChange={e => setRole(e.target.value)}>
          {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
      </Field>
      {isEdit && (
        <Field label="Status">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} className="w-4 h-4 rounded" />
            <span className="text-sm text-gray-300">Active</span>
          </label>
        </Field>
      )}
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
        <button type="submit" disabled={busy} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors">
          {busy ? <Loader size={14} className="animate-spin" /> : <Save size={14} />}
          {isEdit ? 'Save' : 'Create'}
        </button>
      </div>
    </form>
  )
}

export default function Users({ currentUser, onLogout }) {
  const [users,     setUsers]     = useState([])
  const [loading,   setLoading]   = useState(true)
  const [modal,     setModal]     = useState(null)  // null | 'create' | User object

  const isAdmin = currentUser.role === 'admin'

  async function load() {
    try { setUsers(await listUsers()) }
    catch { setUsers([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function handleCreate(body) { await createUser(body); await load() }
  async function handleUpdate(user, body) { await updateUser(user.id, body); await load() }
  async function handleDelete(user) {
    if (!confirm(`Delete user "${user.username}"? This cannot be undone.`)) return
    await deleteUser(user.id); await load()
  }

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-blue-400" size={24} />
          <div>
            <h1 className="text-lg font-semibold text-gray-100">UserManager</h1>
            <p className="text-xs text-gray-500">Signed in as <span className={ROLE_COLOURS[currentUser.role]}>{currentUser.username} ({currentUser.role})</span></p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && (
            <button
              onClick={() => setModal('create')}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-3 py-2 text-sm font-medium transition-colors"
            >
              <Plus size={16} /> New user
            </button>
          )}
          <button onClick={onLogout} className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 px-3 py-2 transition-colors">
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                <th className="text-left px-4 py-3">User</th>
                <th className="text-left px-4 py-3">Role</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Last login</th>
                <th className="text-left px-4 py-3">Created</th>
                {isAdmin && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody>
              {users.map((u, i) => (
                <tr key={u.id} className={`border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors ${i === users.length - 1 ? 'border-b-0' : ''}`}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-100">{u.display_name ?? u.username}</div>
                    {u.display_name && <div className="text-xs text-gray-500">@{u.username}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`font-medium ${ROLE_COLOURS[u.role] ?? 'text-gray-400'}`}>{u.role}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                      {u.is_active ? 'active' : 'inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {u.last_login ? new Date(u.last_login).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setModal(u)} className="p-1.5 text-gray-500 hover:text-blue-400 transition-colors rounded">
                          <Pencil size={14} />
                        </button>
                        {u.id !== currentUser.id && (
                          <button onClick={() => handleDelete(u)} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded">
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal === 'create' && (
        <Modal title="New user" onClose={() => setModal(null)}>
          <UserForm onSave={handleCreate} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal && modal !== 'create' && (
        <Modal title={`Edit — ${modal.username}`} onClose={() => setModal(null)}>
          <UserForm initial={modal} onSave={body => handleUpdate(modal, body)} onClose={() => setModal(null)} />
        </Modal>
      )}
    </div>
  )
}
