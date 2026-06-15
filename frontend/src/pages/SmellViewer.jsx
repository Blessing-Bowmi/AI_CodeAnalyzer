import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getSmells } from '../services/api'

export default function SmellViewer() {
    const { id } = useParams()
    const [smells, setSmells] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [filter, setFilter] = useState('all')

    useEffect(() => {
        const load = async () => {
            try {
                const { data } = await getSmells(id)
                setSmells(data)
            } catch (err) {
                console.error(err)
                setError(true)
            }
            setLoading(false)
        }
        load()
    }, [id])

    const smellTypes = [...new Set(smells.map(s => s.smell_type))]
    const filtered = filter === 'all' ? smells : smells.filter(s => s.smell_type === filter)

    const severityCount = { high: 0, medium: 0, low: 0 }
    smells.forEach(s => { severityCount[s.severity] = (severityCount[s.severity] || 0) + 1 })

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Detecting code smells...</div></div>

    if (error) return (
        <div style={{ textAlign: 'center', padding: 40, marginTop: 40, color: 'var(--text-muted)' }} className="card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
            <h3>Project Not Found</h3>
            <p>This project has been deleted or does not exist. Please select a valid project from the Dashboard.</p>
        </div>
    )

    return (
        <div>
            <div className="page-header">
                <h2>Code Smell Viewer</h2>
                <p>File-wise code smell analysis with severity indicators</p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon amber">🔍</div>
                    <div><div className="stat-value">{smells.length}</div><div className="stat-label">Total Smells</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red">🔴</div>
                    <div><div className="stat-value">{severityCount.high}</div><div className="stat-label">High Severity</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon amber">🟡</div>
                    <div><div className="stat-value">{severityCount.medium}</div><div className="stat-label">Medium</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">🟢</div>
                    <div><div className="stat-value">{severityCount.low}</div><div className="stat-label">Low</div></div>
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    <span className="card-title">Detected Smells</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                        <button className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setFilter('all')}>All</button>
                        {smellTypes.map(t => (
                            <button key={t} className={`btn btn-sm ${filter === t ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setFilter(t)}>{t}</button>
                        ))}
                    </div>
                </div>

                {filtered.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>✨</div>
                        <p>No code smells detected!</p>
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr><th>File</th><th>Type</th><th>Severity</th><th>Line</th><th>Description</th><th>Suggestion</th></tr>
                        </thead>
                        <tbody>
                            {filtered.map((s, i) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 500, color: 'var(--text-primary)', maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.file_name}</td>
                                    <td><span className="badge badge-medium">{s.smell_type}</span></td>
                                    <td><span className={`badge badge-${s.severity}`}>{s.severity}</span></td>
                                    <td>{s.line || '—'}</td>
                                    <td style={{ maxWidth: 250, fontSize: 12 }}>{s.description}</td>
                                    <td style={{ maxWidth: 200, fontSize: 12, color: 'var(--success)' }}>{s.suggestion || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
