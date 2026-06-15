import React, { useState, useEffect } from 'react'
import { getAdminActivity } from '../services/api'

const actionIcons = {
    change_role: '✏️',
    delete_user: '🗑️',
    delete_project: '📦',
}

const actionColors = {
    change_role: 'var(--warning)',
    delete_user: 'var(--danger)',
    delete_project: 'var(--danger)',
}

export default function AdminActivity() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')

    useEffect(() => {
        const load = async () => {
            try {
                const { data } = await getAdminActivity()
                setLogs(data)
            } catch (err) { console.error(err) }
            setLoading(false)
        }
        load()
    }, [])

    const actionTypes = [...new Set(logs.map(l => l.action))]
    const filtered = filter === 'all' ? logs : logs.filter(l => l.action === filter)

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading activity log...</div></div>

    return (
        <div>
            <div className="page-header">
                <h2>📋 Admin Activity Log</h2>
                <p>Track all administrative actions performed on the system</p>
            </div>

            <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                <div className="stat-card">
                    <div className="stat-icon purple">📋</div>
                    <div><div className="stat-value">{logs.length}</div><div className="stat-label">Total Actions</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon amber">✏️</div>
                    <div><div className="stat-value">{logs.filter(l => l.action === 'change_role').length}</div><div className="stat-label">Role Changes</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red">🗑️</div>
                    <div><div className="stat-value">{logs.filter(l => l.action.startsWith('delete')).length}</div><div className="stat-label">Deletions</div></div>
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    <span className="card-title">Activity Timeline</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                        <button className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setFilter('all')}>All</button>
                        {actionTypes.map(a => (
                            <button key={a} className={`btn btn-sm ${filter === a ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setFilter(a)}>
                                {a.replace('_', ' ')}
                            </button>
                        ))}
                    </div>
                </div>

                {filtered.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
                        <p>No admin activity recorded yet.</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {filtered.map((log, i) => (
                            <div key={i} style={{
                                padding: '14px 16px',
                                background: 'var(--bg-surface)',
                                borderRadius: 8,
                                borderLeft: `3px solid ${actionColors[log.action] || 'var(--primary)'}`,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 14
                            }}>
                                <div style={{ fontSize: 20, width: 32, textAlign: 'center' }}>
                                    {actionIcons[log.action] || '📌'}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>
                                        {log.details}
                                    </div>
                                    <div style={{ display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                                        <span>By: <strong>{log.admin_name}</strong></span>
                                        <span>Target: {log.target_type} #{log.target_id}</span>
                                    </div>
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'right', minWidth: 100 }}>
                                    {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
