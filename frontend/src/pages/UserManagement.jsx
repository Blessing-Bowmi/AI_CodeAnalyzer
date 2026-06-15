import React, { useState, useEffect } from 'react'
import { getAdminUsers, updateUserRole, deleteUser } from '../services/api'

export default function UserManagement() {
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')
    const [editingRole, setEditingRole] = useState(null)
    const [toast, setToast] = useState(null)

    useEffect(() => { loadUsers() }, [])

    const loadUsers = async () => {
        try {
            const { data } = await getAdminUsers()
            setUsers(data)
        } catch (err) { console.error(err) }
        setLoading(false)
    }

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type })
        setTimeout(() => setToast(null), 3000)
    }

    const handleRoleChange = async (userId, newRole) => {
        try {
            await updateUserRole(userId, newRole)
            setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u))
            setEditingRole(null)
            showToast(`Role updated to ${newRole}`)
        } catch (err) {
            showToast(err.response?.data?.detail || 'Failed to update role', 'error')
        }
    }

    const handleDelete = async (userId, userName) => {
        if (!confirm(`Delete user "${userName}" and ALL their projects? This cannot be undone.`)) return
        try {
            await deleteUser(userId)
            setUsers(users.filter(u => u.id !== userId))
            showToast(`User "${userName}" deleted`)
        } catch (err) {
            showToast(err.response?.data?.detail || 'Failed to delete user', 'error')
        }
    }

    const filtered = filter === 'all' ? users : users.filter(u => u.role === filter)
    const roleCounts = { all: users.length }
    users.forEach(u => { roleCounts[u.role] = (roleCounts[u.role] || 0) + 1 })

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading users...</div></div>

    return (
        <div>
            {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

            <div className="page-header">
                <h2>👥 User Management</h2>
                <p>Manage all registered users, roles, and permissions</p>
            </div>

            {/* Stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon purple">👥</div>
                    <div><div className="stat-value">{users.length}</div><div className="stat-label">Total Users</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue">💻</div>
                    <div><div className="stat-value">{roleCounts.developer || 0}</div><div className="stat-label">Developers</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red">🛡️</div>
                    <div><div className="stat-value">{roleCounts.admin || 0}</div><div className="stat-label">Admins</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">👁️</div>
                    <div><div className="stat-value">{roleCounts.reviewer || 0}</div><div className="stat-label">Reviewers</div></div>
                </div>
            </div>

            {/* User Table */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">All Users</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                        {['all', 'developer', 'admin', 'reviewer'].map(r => (
                            <button
                                key={r}
                                className={`btn btn-sm ${filter === r ? 'btn-primary' : 'btn-ghost'}`}
                                onClick={() => setFilter(r)}
                            >
                                {r.charAt(0).toUpperCase() + r.slice(1)} ({roleCounts[r] || 0})
                            </button>
                        ))}
                    </div>
                </div>

                <table className="data-table">
                    <thead>
                        <tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Projects</th><th>Joined</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                        {filtered.map(u => (
                            <tr key={u.id}>
                                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>#{u.id}</td>
                                <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{u.name}</td>
                                <td style={{ fontSize: 12 }}>{u.email}</td>
                                <td>
                                    {editingRole === u.id ? (
                                        <div style={{ display: 'flex', gap: 4 }}>
                                            {['developer', 'admin', 'reviewer'].map(r => (
                                                <button
                                                    key={r}
                                                    className={`btn btn-sm ${u.role === r ? 'btn-primary' : 'btn-ghost'}`}
                                                    onClick={() => handleRoleChange(u.id, r)}
                                                    style={{ padding: '3px 8px', fontSize: 11 }}
                                                >
                                                    {r}
                                                </button>
                                            ))}
                                            <button className="btn btn-sm btn-ghost" onClick={() => setEditingRole(null)} style={{ padding: '3px 6px', fontSize: 11 }}>✕</button>
                                        </div>
                                    ) : (
                                        <span
                                            className={`badge ${u.role === 'admin' ? 'badge-high' : u.role === 'reviewer' ? 'badge-medium' : 'badge-low'}`}
                                            style={{ cursor: 'pointer' }}
                                            onClick={() => setEditingRole(u.id)}
                                            title="Click to change role"
                                        >
                                            {u.role}
                                        </span>
                                    )}
                                </td>
                                <td>{u.project_count || 0}</td>
                                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                                </td>
                                <td>
                                    <div style={{ display: 'flex', gap: 4 }}>
                                        <button className="btn btn-ghost btn-sm" onClick={() => setEditingRole(u.id)} title="Change Role" style={{ padding: '4px 8px' }}>✏️</button>
                                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(u.id, u.name)} title="Delete User" style={{ padding: '4px 8px' }}>🗑️</button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {filtered.length === 0 && (
                    <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)', fontSize: 13 }}>
                        No users found with role "{filter}"
                    </div>
                )}
            </div>
        </div>
    )
}
