import { useState, useEffect } from 'react'
import Login from './Login.jsx'
import Users from './Users.jsx'
import { getMe } from './api.js'

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('um_token')) { setLoading(false); return }
    getMe()
      .then(setUser)
      .catch(() => { localStorage.removeItem('um_token'); })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!user) return <Login onLogin={setUser} />

  return <Users currentUser={user} onLogout={() => { localStorage.removeItem('um_token'); setUser(null) }} />
}
