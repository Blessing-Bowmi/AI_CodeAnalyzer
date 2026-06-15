import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadProject } from '../services/api'

export default function Upload() {
    const [file, setFile] = useState(null)
    const [dragging, setDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const navigate = useNavigate()

    const handleDrop = (e) => {
        e.preventDefault()
        setDragging(false)
        const f = e.dataTransfer.files[0]
        if (f && f.name.endsWith('.zip')) setFile(f)
        else setError('Please upload a ZIP file')
    }

    const handleFileChange = (e) => {
        const f = e.target.files[0]
        if (f) setFile(f)
    }

    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setError('')
        try {
            const { data } = await uploadProject(file)
            setResult(data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed')
        }
        setUploading(false)
    }

    return (
        <div>
            <div className="page-header">
                <h2>Upload Project</h2>
                <p>Upload a ZIP file containing your source code for analysis</p>
            </div>

            {result ? (
                <div className="card" style={{ textAlign: 'center', padding: 40 }}>
                    <div style={{ fontSize: 64, marginBottom: 16 }}>✅</div>
                    <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Upload Successful!</h3>
                    <p style={{ color: 'var(--text-muted)', marginBottom: 20 }}>
                        <strong>{result.project_name}</strong> — {result.files_extracted} files extracted
                    </p>
                    <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                        <button className="btn btn-primary" onClick={() => navigate('/')}>Go to Dashboard</button>
                        <button className="btn btn-ghost" onClick={() => { setResult(null); setFile(null) }}>Upload Another</button>
                    </div>
                </div>
            ) : (
                <div className="card">
                    <div
                        className={`upload-zone ${dragging ? 'dragging' : ''}`}
                        onDragOver={e => { e.preventDefault(); setDragging(true) }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('fileInput').click()}
                    >
                        <div className="upload-zone-icon">📁</div>
                        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
                            {file ? file.name : 'Drop your ZIP file here'}
                        </h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                            {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'or click to browse'}
                        </p>
                        <input id="fileInput" type="file" accept=".zip" onChange={handleFileChange} style={{ display: 'none' }} />
                    </div>

                    {error && <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginTop: 16 }}>{error}</div>}

                    {file && (
                        <div style={{ marginTop: 20, display: 'flex', gap: 12, justifyContent: 'center' }}>
                            <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
                                {uploading ? '⏳ Uploading...' : '🚀 Upload & Analyze'}
                            </button>
                            <button className="btn btn-ghost" onClick={() => setFile(null)}>Clear</button>
                        </div>
                    )}

                    <div style={{ marginTop: 24, padding: 16, background: 'var(--bg-surface)', borderRadius: 8 }}>
                        <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Supported Languages</h4>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {['Python', 'JavaScript', 'TypeScript', 'Java', 'C/C++', 'C#', 'Ruby', 'Go', 'PHP'].map(lang => (
                                <span key={lang} className="badge badge-low">{lang}</span>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
