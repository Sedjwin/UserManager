import { useState } from 'react'
import { LogIn } from 'lucide-react'
import { login } from './api.js'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [busy, setBusy]         = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const data = await login(username, password)
      localStorage.setItem('um_token', data.access_token)
      onLogin({ id: data.user_id, username: data.username, role: data.role })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={submit} className="bg-gray-900 border border-gray-800 rounded-2xl p-8 w-full max-w-sm space-y-5">
        <div>
          <h1 className="text-xl font-semibold text-gray-100">UserManager</h1>
          <p className="text-sm text-gray-500 mt-1">Sign in to manage users</p>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <input
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
          placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required autoFocus
        />
        <input
          type="password"
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
          placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required
        />
        <button
          type="submit" disabled={busy}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          <LogIn size={16} /> {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
