import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/api'

export default function Register({ onLogin }) {
    const [form, setForm] = useState({ name: '', email: '', password: '', role: 'developer' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const { data } = await register(form)
            onLogin(data.user, data.token)
            navigate('/')
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed')
        }
        setLoading(false)
    }

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h1 className="auth-title">⚡ CodeAnalyzer</h1>
                <p className="auth-subtitle">Create your account</p>
                {error && <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 16 }}>{error}</div>}
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Full Name</label>
                        <input className="form-input" type="text" placeholder="John Doe" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input className="form-input" type="email" placeholder="you@example.com" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input className="form-input" type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Role</label>
                        <select className="form-input" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                            <option value="developer">Developer</option>
                            <option value="reviewer">Reviewer</option>
                        </select>
                    </div>
                    <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }} disabled={loading}>
                        {loading ? 'Creating Account...' : 'Create Account'}
                    </button>
                </form>
                <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-muted)' }}>
                    Already have an account? <Link to="/login" style={{ color: 'var(--primary-light)' }}>Sign In</Link>
                </p>
                <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(99,102,241,0.08)', borderRadius: 8, textAlign: 'center', fontSize: 12, color: 'var(--text-muted)' }}>
                    🛡️ Admin? Use the default admin credentials to <Link to="/login" style={{ color: 'var(--primary-light)' }}>Sign In</Link>
                </div>
            </div>
        </div>
    )
}
