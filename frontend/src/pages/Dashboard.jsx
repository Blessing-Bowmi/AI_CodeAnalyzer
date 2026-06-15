import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProjects, deleteProject, analyzeProject } from '../services/api'

export default function Dashboard({ user }) {
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const [analyzing, setAnalyzing] = useState(null)
    const navigate = useNavigate()

    const isDeveloper = user?.role === 'developer'
    const isAdmin = user?.role === 'admin'

    useEffect(() => { loadProjects() }, [])

    const loadProjects = async () => {
        try {
            const { data } = await getProjects()
            setProjects(data)
        } catch (err) { console.error(err) }
        setLoading(false)
    }

    const handleAnalyze = async (id) => {
        setAnalyzing(id)
        try {
            await analyzeProject(id)
            await loadProjects()
        } catch (err) { console.error(err) }
        setAnalyzing(null)
    }

    const handleDelete = async (id) => {
        if (!confirm('Delete this project and all data?')) return
        try {
            await deleteProject(id)
            setProjects(projects.filter(p => p.id !== id))
        } catch (err) { console.error(err) }
    }

    const totalFiles = projects.reduce((s, p) => s + (p.total_files || 0), 0)
    const avgScore = projects.length ? Math.round(projects.reduce((s, p) => s + (p.quality_score || 0), 0) / projects.length) : 0

    return (
        <div>
            <div className="page-header">
                <h2>Dashboard</h2>
                <p>Overview of your projects and code quality metrics</p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon purple">📦</div>
                    <div><div className="stat-value">{projects.length}</div><div className="stat-label">Projects</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue">📄</div>
                    <div><div className="stat-value">{totalFiles}</div><div className="stat-label">Total Files</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">⭐</div>
                    <div><div className="stat-value">{avgScore}</div><div className="stat-label">Avg Quality Score</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon pink">🔧</div>
                    <div>
                        <div className="stat-value">{projects.reduce((s, p) => s + (p.total_functions || 0), 0)}</div>
                        <div className="stat-label">Total Functions</div>
                    </div>
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    <span className="card-title">{isDeveloper ? 'Your Projects' : 'All Projects'}</span>
                    {isDeveloper && <button className="btn btn-primary btn-sm" onClick={() => navigate('/upload')}>+ Upload New</button>}
                </div>

                {loading ? <div className="loading-spinner" /> : projects.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
                        <p>{isDeveloper ? 'No projects yet. Upload a ZIP file to get started.' : 'No projects available in the system yet.'}</p>
                        {isDeveloper && <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/upload')}>Upload Project</button>}
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Project</th>
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
                                            {isDeveloper && (
                                                <button className="btn btn-primary btn-sm" onClick={() => handleAnalyze(p.id)} disabled={analyzing === p.id}>
                                                    {analyzing === p.id ? '⏳ Analyzing...' : '🔬 Analyze'}
                                                </button>
                                            )}
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
        </div>
    )
}
