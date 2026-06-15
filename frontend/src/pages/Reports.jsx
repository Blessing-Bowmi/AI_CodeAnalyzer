import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getJsonReport, getPdfReport } from '../services/api'
import ReviewComments from '../components/ReviewComments'

export default function Reports({ user }) {
    const { id } = useParams()
    const [report, setReport] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [downloading, setDownloading] = useState(false)

    useEffect(() => {
        const load = async () => {
            try {
                const { data } = await getJsonReport(id)
                setReport(data)
            } catch (err) {
                console.error(err)
                setError(true)
            }
            setLoading(false)
        }
        load()
    }, [id])

    const handleDownloadPdf = async () => {
        setDownloading(true)
        try {
            const { data } = await getPdfReport(id)
            const url = window.URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
            const link = document.createElement('a')
            link.href = url
            link.download = `report_project_${id}.pdf`
            link.click()
            window.URL.revokeObjectURL(url)
        } catch (err) { console.error(err) }
        setDownloading(false)
    }

    const handleDownloadJson = () => {
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `report_project_${id}.json`
        link.click()
        window.URL.revokeObjectURL(url)
    }

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Generating report...</div></div>

    if (error) return (
        <div style={{ textAlign: 'center', padding: 40, marginTop: 40, color: 'var(--text-muted)' }} className="card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
            <h3>Project Not Found</h3>
            <p>This project has been deleted or does not exist. Please select a valid project from the Dashboard.</p>
        </div>
    )

    if (!report) return (
        <div>
            <div className="page-header"><h2>Reports</h2></div>
            <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <p>No report data. Run analysis first.</p>
            </div>
        </div>
    )

    const scoreColor = (report.code_quality?.score || 0) >= 70 ? 'var(--success)' : (report.code_quality?.score || 0) >= 40 ? 'var(--warning)' : 'var(--danger)'

    return (
        <div>
            <div className="page-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2>Reports</h2>
                        <p>Download comprehensive PDF and JSON reports</p>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-primary" onClick={handleDownloadPdf} disabled={downloading}>
                            {downloading ? '⏳ Generating...' : '📥 Download PDF'}
                        </button>
                        <button className="btn btn-ghost" onClick={handleDownloadJson}>📥 Download JSON</button>
                    </div>
                </div>
            </div>

            {/* Overview */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="score-circle" style={{ width: 60, height: 60, border: `3px solid ${scoreColor}` }}>
                        <div style={{ fontSize: 18, fontWeight: 800, color: scoreColor }}>{report.code_quality?.score || 0}</div>
                    </div>
                    <div><div className="stat-value">{report.code_quality?.grade || '—'}</div><div className="stat-label">Quality Grade</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue">📄</div>
                    <div><div className="stat-value">{report.project?.total_files || 0}</div><div className="stat-label">Files</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon purple">📏</div>
                    <div><div className="stat-value">{report.project?.total_loc || 0}</div><div className="stat-label">Lines of Code</div></div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red">🔍</div>
                    <div><div className="stat-value">{report.smells?.total || 0}</div><div className="stat-label">Smells</div></div>
                </div>
            </div>

            {/* Smells Breakdown */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="card">
                    <div className="card-title" style={{ marginBottom: 16 }}>Smells by Type</div>
                    {report.smells?.by_type && Object.entries(report.smells.by_type).map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ fontSize: 13 }}>{key}</span>
                            <span className="badge badge-medium">{val}</span>
                        </div>
                    ))}
                </div>

                <div className="card">
                    <div className="card-title" style={{ marginBottom: 16 }}>Smells by Severity</div>
                    {report.smells?.by_severity && Object.entries(report.smells.by_severity).map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{key}</span>
                            <span className={`badge badge-${key}`}>{val}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Refactoring Summary */}
            <div className="card" style={{ marginTop: 16 }}>
                <div className="card-title" style={{ marginBottom: 16 }}>Refactoring History</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                    {report.refactoring?.by_status && Object.entries(report.refactoring.by_status).map(([key, val]) => (
                        <div key={key} style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                            <div style={{ fontSize: 24, fontWeight: 800 }}>{val}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{key}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Dependencies */}
            <div className="card" style={{ marginTop: 16 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>Dependency Summary</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                    <div style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                        <div style={{ fontSize: 24, fontWeight: 800 }}>{report.dependencies?.total || 0}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total</div>
                    </div>
                    <div style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                        <div style={{ fontSize: 24, fontWeight: 800 }}>{report.dependencies?.module_deps || 0}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Module Deps</div>
                    </div>
                    <div style={{ padding: 16, background: 'var(--bg-surface)', borderRadius: 8, textAlign: 'center' }}>
                        <div style={{ fontSize: 24, fontWeight: 800 }}>{report.dependencies?.function_calls || 0}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Function Calls</div>
                    </div>
                </div>
            </div>

            {/* Review Comments */}
            <ReviewComments projectId={id} user={user} />

            {/* Report metadata */}
            <div style={{ marginTop: 16, padding: 12, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                Report generated on {report.report_date ? new Date(report.report_date).toLocaleString() : '—'}
            </div>
        </div>
    )
}
