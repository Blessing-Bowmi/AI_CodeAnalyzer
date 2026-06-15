import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getAllPreviews } from '../services/api'

export default function RefactorPreview() {
    const { id } = useParams()
    const [previews, setPreviews] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [selected, setSelected] = useState(0)

    useEffect(() => {
        const load = async () => {
            try {
                const { data } = await getAllPreviews(id)
                setPreviews(data)
            } catch (err) {
                console.error(err)
                setError(true)
            }
            setLoading(false)
        }
        load()
    }, [id])

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading previews...</div></div>

    if (error) return (
        <div style={{ textAlign: 'center', padding: 40, marginTop: 40, color: 'var(--text-muted)' }} className="card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
            <h3>Project Not Found</h3>
            <p>This project has been deleted or does not exist. Please select a valid project from the Dashboard.</p>
        </div>
    )

    if (previews.length === 0) return (
        <div>
            <div className="page-header"><h2>Refactor Preview</h2><p>Before vs After code comparison</p></div>
            <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>👁️</div>
                <p>No refactoring previews available. Run analysis and check suggestions first.</p>
            </div>
        </div>
    )

    const current = previews[selected]

    return (
        <div>
            <div className="page-header">
                <h2>Refactor Preview</h2>
                <p>Visual diff view — Before vs After code comparison</p>
            </div>

            {/* Preview selector */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
                {previews.map((p, i) => (
                    <button
                        key={i}
                        className={`btn btn-sm ${i === selected ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setSelected(i)}
                    >
                        {p.refactor_type} — {p.file_name}
                    </button>
                ))}
            </div>

            {current && (
                <>
                    {/* Stats */}
                    <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                        <div className="stat-card">
                            <div className="stat-icon green">➕</div>
                            <div><div className="stat-value">{current.stats?.lines_added || 0}</div><div className="stat-label">Lines Added</div></div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon red">➖</div>
                            <div><div className="stat-value">{current.stats?.lines_removed || 0}</div><div className="stat-label">Lines Removed</div></div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon blue">〰️</div>
                            <div><div className="stat-value">{current.stats?.lines_unchanged || 0}</div><div className="stat-label">Unchanged</div></div>
                        </div>
                    </div>

                    <div style={{ marginBottom: 12, fontSize: 14 }}>
                        <strong>{current.refactor_type}</strong> — <span style={{ color: 'var(--text-muted)' }}>{current.description}</span>
                    </div>

                    {/* Side by side */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div className="card">
                            <div className="card-title" style={{ marginBottom: 12, color: 'var(--danger)' }}>❌ Before</div>
                            <pre style={{ background: 'var(--bg-surface)', padding: 16, borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: 400, color: 'var(--text-secondary)' }}>
                                {current.before || 'No code'}
                            </pre>
                        </div>
                        <div className="card">
                            <div className="card-title" style={{ marginBottom: 12, color: 'var(--success)' }}>✅ After</div>
                            <pre style={{ background: 'var(--bg-surface)', padding: 16, borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: 400, color: 'var(--text-secondary)' }}>
                                {current.after || 'No code'}
                            </pre>
                        </div>
                    </div>

                    {/* Unified Diff */}
                    <div className="card" style={{ marginTop: 16 }}>
                        <div className="card-title" style={{ marginBottom: 12 }}>📝 Unified Diff View</div>
                        <div className="diff-container">
                            {current.changes?.map((c, i) => (
                                <div key={i} className={`diff-line ${c.type === 'added' ? 'diff-added' : c.type === 'removed' ? 'diff-removed' : 'diff-unchanged'}`}>
                                    <span style={{ marginRight: 8, opacity: 0.5 }}>
                                        {c.type === 'added' ? '+' : c.type === 'removed' ? '-' : ' '}
                                    </span>
                                    {c.content}
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
