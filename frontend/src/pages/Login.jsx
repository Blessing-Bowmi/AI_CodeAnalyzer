import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../services/api'

export default function Login({ onLogin }) {
    const [form, setForm] = useState({ email: '', password: '' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const { data } = await login(form)
            onLogin(data.user, data.token)
            navigate('/')
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed')
        }
        setLoading(false)
    }

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h1 className="auth-title">⚡ CodeAnalyzer</h1>
                <p className="auth-subtitle">Sign in to your account</p>
                {error && <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 16 }}>{error}</div>}
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input className="form-input" type="email" placeholder="you@example.com" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input className="form-input" type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
                    </div>
                    <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }} disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
                <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-muted)' }}>
                    Don't have an account? <Link to="/register" style={{ color: 'var(--primary-light)' }}>Register</Link>
                </p>
            </div>
        </div>
    )
}
