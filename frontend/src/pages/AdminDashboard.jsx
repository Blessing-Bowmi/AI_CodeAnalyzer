import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAdminDashboard, getProjects, deleteProject } from '../services/api'

export default function AdminDashboard() {
    const [data, setData] = useState(null)
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()

    useEffect(() => {
        const load = async () => {
            try {
                const [dashRes, projRes] = await Promise.all([getAdminDashboard(), getProjects()])
                setData(dashRes.data)
                setProjects(projRes.data)
            } catch (err) { console.error(err) }
            setLoading(false)
        }
        load()
    }, [])

    const handleDelete = async (id) => {
        if (!confirm('Delete this project and all associated data?')) return
        try {
            await deleteProject(id)
            setProjects(projects.filter(p => p.id !== id))
            setData(prev => ({
                ...prev,
                stats: { ...prev.stats, total_projects: prev.stats.total_projects - 1 }
            }))
        } catch (err) { console.error(err) }
    }

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading admin dashboard...</div></div>
    if (!data) return <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Failed to load dashboard</div>

    const { stats, role_breakdown, refactor_breakdown, smell_breakdown, recent_users } = data

    return (
        <div>
            {/* Header */}
            <div className="page-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2>🛡️ Admin Dashboard</h2>
                        <p>System-wide overview and management</p>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-primary btn-sm" onClick={() => navigate('/admin/users')}>👥 Manage Users</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/admin/analytics')}>📊 Analytics</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/admin/activity')}>📋 Activity Log</button>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon purple">👥</div>
                    <div><div className="stat-value">{stats.total_users}</div><div className="stat-label">Total Users</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue">📦</div>
                    <div><div className="stat-value">{stats.total_projects}</div><div className="stat-label">Total Projects</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">📄</div>
                    <div><div className="stat-value">{stats.total_files}</div><div className="stat-label">Total Files</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon amber">🔍</div>
                    <div><div className="stat-value">{stats.total_smells}</div><div className="stat-label">Code Smells</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon pink">🔧</div>
                    <div><div className="stat-value">{stats.total_refactors}</div><div className="stat-label">Refactorings</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue">🤖</div>
                    <div><div className="stat-value">{stats.total_ai_suggestions}</div><div className="stat-label">AI Suggestions</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">⭐</div>
                    <div><div className="stat-value">{stats.avg_quality_score}</div><div className="stat-label">Avg Quality</div></div>
                </div>
            </div>

            {/* Breakdowns */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
                <div className="card">
                    <div className="card-title" style={{ marginBottom: 12 }}>👥 Users by Role</div>
                    {Object.entries(role_breakdown).map(([role, count]) => (
                        <div key={role} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{role}</span>
                            <span className="badge badge-low">{count}</span>
                        </div>
                    ))}
                </div>

                <div className="card">
                    <div className="card-title" style={{ marginBottom: 12 }}>🔍 Smells by Severity</div>
                    {Object.entries(smell_breakdown).map(([sev, count]) => (
                        <div key={sev} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{sev}</span>
                            <span className={`badge badge-${sev}`}>{count}</span>
                        </div>
                    ))}
                </div>

                <div className="card">
                    <div className="card-title" style={{ marginBottom: 12 }}>🔧 Refactorings by Status</div>
                    {Object.entries(refactor_breakdown).map(([status, count]) => (
                        <div key={status} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{status}</span>
                            <span className={`badge ${status === 'applied' ? 'badge-low' : status === 'rejected' ? 'badge-high' : 'badge-medium'}`}>{count}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* All Projects — Full interactive table */}
            <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-header">
                    <span className="card-title">📦 All Projects</span>
                    <span className="badge badge-low">{projects.length} total</span>
                </div>
                {projects.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
                        <p>No projects uploaded by any developer yet.</p>
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Project</th>
                                <th>Owner</th>
                                <th>Files</th>
                                <th>Quality</th>
                                <th>Upload Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {projects.map(p => (
                                <tr key={p.id}>
                                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{p.project_name}</td>
                                    <td style={{ fontSize: 12 }}>{p.owner_name || '—'}</td>
                                    <td>{p.total_files || 0}</td>
                                    <td>
                                        {p.quality_score > 0 ? (
                                            <span className={`badge ${p.quality_score >= 70 ? 'badge-low' : p.quality_score >= 40 ? 'badge-medium' : 'badge-high'}`}>
                                                {p.quality_score}/100
                                            </span>
                                        ) : (
                                            <span className="badge" style={{ background: 'var(--bg-surface)', color: 'var(--text-muted)' }}>
                                                Unanalyzed
                                            </span>
                                        )}
                                    </td>
                                    <td style={{ fontSize: 12 }}>{p.upload_date ? new Date(p.upload_date).toLocaleDateString() : '—'}</td>
                                    <td>
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/dependencies/${p.id}`)}>📊 View</button>
                                            <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/smells/${p.id}`)}>🔍 Smells</button>
                                            <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/refactor/${p.id}`)}>🔧</button>
                                            <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/reports/${p.id}`)}>📄</button>
                                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id)}>🗑️</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Recent Users */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">👤 Recent Users</span>
                    <button className="btn btn-ghost btn-sm" onClick={() => navigate('/admin/users')}>Manage →</button>
                </div>
                {recent_users.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No users yet</div>
                ) : (
                    <table className="data-table">
                        <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
                        <tbody>
                            {recent_users.slice(0, 5).map(u => (
                                <tr key={u.id}>
                                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{u.name}</td>
                                    <td style={{ fontSize: 12 }}>{u.email}</td>
                                    <td><span className={`badge ${u.role === 'admin' ? 'badge-high' : u.role === 'reviewer' ? 'badge-medium' : 'badge-low'}`}>{u.role}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}

