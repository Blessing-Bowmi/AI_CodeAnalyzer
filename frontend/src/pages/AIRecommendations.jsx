import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getRecommendations, getMaintainability } from '../services/api'

export default function AIRecommendations() {
    const { id } = useParams()
    const [suggestions, setSuggestions] = useState([])
    const [score, setScore] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)

    useEffect(() => {
        const load = async () => {
            try {
                const [recRes, maintRes] = await Promise.all([getRecommendations(id), getMaintainability(id)])
                setSuggestions(recRes.data)
                setScore(maintRes.data)
            } catch (err) {
                console.error(err)
                setError(true)
            }
            setLoading(false)
        }
        load()
    }, [id])

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Generating AI recommendations...</div></div>

    if (error) return (
        <div style={{ textAlign: 'center', padding: 40, marginTop: 40, color: 'var(--text-muted)' }} className="card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
            <h3>Project Not Found</h3>
            <p>This project has been deleted or does not exist. Please select a valid project from the Dashboard.</p>
        </div>
    )

    const scoreColor = score?.score >= 70 ? 'var(--success)' : score?.score >= 40 ? 'var(--warning)' : 'var(--danger)'

    return (
        <div>
            <div className="page-header">
                <h2>🤖 AI Recommendations</h2>
                <p>ML-powered insights, maintainability scoring, and smart suggestions</p>
            </div>

            {/* Maintainability Score */}
            {score && (
                <div className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title" style={{ marginBottom: 16 }}>Maintainability Score</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
                        <div className="score-circle" style={{ border: `4px solid ${scoreColor}`, boxShadow: `0 0 20px ${scoreColor}33` }}>
                            <div className="score-value" style={{ color: scoreColor }}>{score.score}</div>
                            <div className="score-label">/ 100</div>
                        </div>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 36, fontWeight: 800, marginBottom: 4, color: scoreColor }}>{score.grade}</div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 16 }}>
                                {score.breakdown && Object.entries(score.breakdown).map(([key, val]) => (
                                    <div key={key} style={{ padding: 12, background: 'var(--bg-surface)', borderRadius: 8 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                                            <span style={{ fontSize: 12, fontWeight: 600, textTransform: 'capitalize' }}>{key}</span>
                                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{val.score}/{val.max}</span>
                                        </div>
                                        <div style={{ height: 4, background: 'var(--border)', borderRadius: 2 }}>
                                            <div style={{ width: `${(val.score / val.max) * 100}%`, height: '100%', background: val.score / val.max > 0.7 ? 'var(--success)' : val.score / val.max > 0.4 ? 'var(--warning)' : 'var(--danger)', borderRadius: 2, transition: 'width 0.5s ease' }} />
                                        </div>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{val.description}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {score.recommendations && (
                        <div style={{ marginTop: 16, padding: 12, background: 'var(--bg-surface)', borderRadius: 8 }}>
                            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Improvement Tips</div>
                            {score.recommendations.map((tip, i) => (
                                <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>{tip}</div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* File Details */}
            {score?.file_details && score.file_details.length > 0 && (
                <div className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title" style={{ marginBottom: 12 }}>File-Level Scores</div>
                    <table className="data-table">
                        <thead>
                            <tr><th>File</th><th>Score</th><th>LOC</th><th>Smells</th><th>Deps</th></tr>
                        </thead>
                        <tbody>
                            {score.file_details.slice(0, 20).map((f, i) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 500 }}>{f.file}</td>
                                    <td><span className={`badge ${f.score >= 70 ? 'badge-low' : f.score >= 40 ? 'badge-medium' : 'badge-high'}`}>{f.score}</span></td>
                                    <td>{f.loc}</td>
                                    <td>{f.smells}</td>
                                    <td>{f.deps}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* AI Suggestions */}
            <div className="card">
                <div className="card-title" style={{ marginBottom: 16 }}>AI Suggestions ({suggestions.length})</div>
                {suggestions.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                        No suggestions yet. Run full analysis from Dashboard first.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {suggestions.map((s, i) => (
                            <div key={i} style={{ padding: 14, background: 'var(--bg-surface)', borderRadius: 8, borderLeft: `3px solid ${s.risk_level === 'high' ? 'var(--danger)' : s.risk_level === 'medium' ? 'var(--warning)' : 'var(--success)'}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: 13, flex: 1 }}>{s.suggestion}</span>
                                    <div style={{ display: 'flex', gap: 6, marginLeft: 12 }}>
                                        <span className={`badge badge-${s.risk_level}`}>{s.risk_level}</span>
                                        <span className="badge badge-low">{Math.round((s.confidence_score || 0) * 100)}%</span>
                                    </div>
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Category: {s.category}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
