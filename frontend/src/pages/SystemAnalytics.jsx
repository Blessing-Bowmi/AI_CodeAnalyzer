import React, { useState, useEffect } from 'react'
import { getSystemAnalytics } from '../services/api'

export default function SystemAnalytics() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const load = async () => {
            try {
                const { data: res } = await getSystemAnalytics()
                setData(res)
            } catch (err) { console.error(err) }
            setLoading(false)
        }
        load()
    }, [])

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading analytics...</div></div>
    if (!data) return <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>No analytics data available</div>

    const maxSmellCount = data.smell_types.length > 0 ? Math.max(...data.smell_types.map(s => s.count)) : 1
    const maxRefactorCount = data.refactor_types.length > 0 ? Math.max(...data.refactor_types.map(r => r.count)) : 1

    return (
        <div>
            <div className="page-header">
                <h2>📊 System Analytics</h2>
                <p>Detailed analytics across all users and projects</p>
            </div>

            {/* AI Acceptance Rate */}
            <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-title" style={{ marginBottom: 16 }}>🤖 AI Suggestion Acceptance</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 30 }}>
                    <div className="score-circle" style={{
                        border: `4px solid ${data.ai_acceptance.rate >= 60 ? 'var(--success)' : data.ai_acceptance.rate >= 30 ? 'var(--warning)' : 'var(--danger)'}`,
                        boxShadow: `0 0 20px ${data.ai_acceptance.rate >= 60 ? 'rgba(34,197,94,0.2)' : 'rgba(245,158,11,0.2)'}`
                    }}>
                        <div className="score-value" style={{ color: data.ai_acceptance.rate >= 60 ? 'var(--success)' : 'var(--warning)' }}>{data.ai_acceptance.rate}%</div>
                        <div className="score-label">accepted</div>
                    </div>
                    <div style={{ flex: 1 }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                            <div style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                                <div style={{ fontSize: 24, fontWeight: 800 }}>{data.ai_acceptance.total}</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total Suggestions</div>
                            </div>
                            <div style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--success)' }}>{data.ai_acceptance.accepted}</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Accepted</div>
                            </div>
                            <div style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--danger)' }}>{data.ai_acceptance.total - data.ai_acceptance.accepted}</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Rejected</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                {/* Smell Types Bar Chart */}
                <div className="card">
                    <div className="card-title" style={{ marginBottom: 16 }}>🔍 Code Smells by Type</div>
                    {data.smell_types.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No smell data yet</div>
                    ) : (
                        data.smell_types.map((s, i) => (
                            <div key={i} style={{ marginBottom: 10 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                    <span style={{ fontSize: 12, fontWeight: 500 }}>{s.smell_type}</span>
                                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.count}</span>
                                </div>
                                <div style={{ height: 6, background: 'var(--border)', borderRadius: 3 }}>
                                    <div style={{
                                        width: `${(s.count / maxSmellCount) * 100}%`,
                                        height: '100%',
                                        background: 'linear-gradient(135deg, var(--warning), var(--danger))',
                                        borderRadius: 3,
                                        transition: 'width 0.5s ease'
                                    }} />
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Refactor Types Bar Chart */}
                <div className="card">
                    <div className="card-title" style={{ marginBottom: 16 }}>🔧 Refactoring Types</div>
                    {data.refactor_types.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No refactoring data yet</div>
                    ) : (
                        data.refactor_types.map((r, i) => (
                            <div key={i} style={{ marginBottom: 10 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                    <span style={{ fontSize: 12, fontWeight: 500 }}>{r.refactor_type}</span>
                                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.count}</span>
                                </div>
                                <div style={{ height: 6, background: 'var(--border)', borderRadius: 3 }}>
                                    <div style={{
                                        width: `${(r.count / maxRefactorCount) * 100}%`,
                                        height: '100%',
                                        background: 'linear-gradient(135deg, var(--primary), var(--primary-dark))',
                                        borderRadius: 3,
                                        transition: 'width 0.5s ease'
                                    }} />
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Top / Worst Quality Projects */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                <div className="card">
                    <div className="card-title" style={{ marginBottom: 12, color: 'var(--success)' }}>🏆 Top Quality Projects</div>
                    {data.top_quality_projects.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No data</div>
                    ) : (
                        <table className="data-table">
                            <thead><tr><th>Project</th><th>Owner</th><th>Score</th></tr></thead>
                            <tbody>
                                {data.top_quality_projects.map((p, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 500 }}>{p.project_name}</td>
                                        <td style={{ fontSize: 12 }}>{p.owner}</td>
                                        <td><span className="badge badge-low">{p.quality_score}</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                <div className="card">
                    <div className="card-title" style={{ marginBottom: 12, color: 'var(--danger)' }}>⚠️ Needs Improvement</div>
                    {data.worst_quality_projects.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No data</div>
                    ) : (
                        <table className="data-table">
                            <thead><tr><th>Project</th><th>Owner</th><th>Score</th></tr></thead>
                            <tbody>
                                {data.worst_quality_projects.map((p, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 500 }}>{p.project_name}</td>
                                        <td style={{ fontSize: 12 }}>{p.owner}</td>
                                        <td><span className="badge badge-high">{p.quality_score}</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Most Active Users */}
            <div className="card">
                <div className="card-title" style={{ marginBottom: 12 }}>🏅 Most Active Users</div>
                {data.most_active_users.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No data</div>
                ) : (
                    <table className="data-table">
                        <thead><tr><th>Rank</th><th>Name</th><th>Email</th><th>Role</th><th>Projects</th></tr></thead>
                        <tbody>
                            {data.most_active_users.map((u, i) => (
                                <tr key={i}>
                                    <td style={{ fontSize: 16, fontWeight: 700 }}>{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}</td>
                                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{u.name}</td>
                                    <td style={{ fontSize: 12 }}>{u.email}</td>
                                    <td><span className={`badge ${u.role === 'admin' ? 'badge-high' : u.role === 'reviewer' ? 'badge-medium' : 'badge-low'}`}>{u.role}</span></td>
                                    <td style={{ fontWeight: 700 }}>{u.projects}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Dependency Types */}
            {data.dependency_types.length > 0 && (
                <div className="card" style={{ marginTop: 16 }}>
                    <div className="card-title" style={{ marginBottom: 12 }}>🔗 Dependency Types</div>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                        {data.dependency_types.map((d, i) => (
                            <div key={i} style={{ padding: '12px 20px', background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                                <div style={{ fontSize: 20, fontWeight: 800 }}>{d.count}</div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{d.type}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
