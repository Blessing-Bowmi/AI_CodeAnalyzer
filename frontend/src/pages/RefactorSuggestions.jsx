import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getRefactorings, applyRefactor, rejectRefactor, getRisk } from '../services/api'

export default function RefactorSuggestions() {
    const { id } = useParams()
    const [refactors, setRefactors] = useState([])
    const [risks, setRisks] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)

    useEffect(() => {
        const load = async () => {
            try {
                const [rRes, rkRes] = await Promise.all([getRefactorings(id), getRisk(id)])
                setRefactors(rRes.data)
                const riskMap = {}
                rkRes.data.risks?.forEach(r => { riskMap[r.refactor_id] = r })
                setRisks(riskMap)
            } catch (err) {
                console.error(err)
                setError(true)
            }
            setLoading(false)
        }
        load()
    }, [id])

    const handleApply = async (refactorId) => {
        try {
            await applyRefactor(id, refactorId)
            setRefactors(refactors.map(r => r.id === refactorId ? { ...r, status: 'applied' } : r))
        } catch (err) { console.error(err) }
    }

    const handleReject = async (refactorId) => {
        try {
            await rejectRefactor(id, refactorId)
            setRefactors(refactors.map(r => r.id === refactorId ? { ...r, status: 'rejected' } : r))
        } catch (err) { console.error(err) }
    }

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading refactoring suggestions...</div></div>

    if (error) return (
        <div style={{ textAlign: 'center', padding: 40, marginTop: 40, color: 'var(--text-muted)' }} className="card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
            <h3>Project Not Found</h3>
            <p>This project has been deleted or does not exist. Please select a valid project from the Dashboard.</p>
        </div>
    )

    const suggested = refactors.filter(r => r.status === 'suggested')
    const applied = refactors.filter(r => r.status === 'applied')
    const rejected = refactors.filter(r => r.status === 'rejected')

    return (
        <div>
            <div className="page-header">
                <h2>Refactor Suggestions</h2>
                <p>One-click auto-refactoring with risk analysis</p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon purple">🔧</div>
                    <div><div className="stat-value">{refactors.length}</div><div className="stat-label">Total Suggestions</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon amber">⏳</div>
                    <div><div className="stat-value">{suggested.length}</div><div className="stat-label">Pending</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">✅</div>
                    <div><div className="stat-value">{applied.length}</div><div className="stat-label">Applied</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red">❌</div>
                    <div><div className="stat-value">{rejected.length}</div><div className="stat-label">Rejected</div></div>
                </div>
            </div>

            {refactors.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: 48, marginBottom: 16 }}>✨</div>
                    <p>No refactoring suggestions. Run analysis first from the Dashboard.</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {refactors.map(r => {
                        const risk = risks[r.id]
                        return (
                            <div key={r.id} className="card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                            <span style={{ fontWeight: 700, fontSize: 15 }}>{r.refactor_type}</span>
                                            <span className={`badge badge-${r.status === 'applied' ? 'low' : r.status === 'rejected' ? 'high' : 'medium'}`}>
                                                {r.status}
                                            </span>
                                            {risk && (
                                                <span className={`badge badge-${risk.risk_level}`}>
                                                    Risk: {risk.risk_score}/100
                                                </span>
                                            )}
                                        </div>
                                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>{r.description}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>📄 {r.file_name}</div>

                                        {risk?.warnings && (
                                            <div style={{ marginTop: 8 }}>
                                                {risk.warnings.map((w, i) => (
                                                    <div key={i} style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>⚠️ {w}</div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {r.status === 'suggested' && (
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            <button className="btn btn-success btn-sm" onClick={() => handleApply(r.id)}>✅ Apply</button>
                                            <button className="btn btn-danger btn-sm" onClick={() => handleReject(r.id)}>❌ Reject</button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
