import React, { useState, useEffect } from 'react'
import { getReviewComments, addReviewComment } from '../services/api'

export default function ReviewComments({ projectId, user }) {
    const [comments, setComments] = useState([])
    const [newComment, setNewComment] = useState('')
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    const canComment = user?.role === 'admin' || user?.role === 'reviewer'

    useEffect(() => {
        loadComments()
    }, [projectId])

    const loadComments = async () => {
        try {
            const { data } = await getReviewComments(projectId)
            setComments(data)
        } catch (err) {
            console.error('Failed to load comments', err)
        }
        setLoading(false)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!newComment.trim()) return

        setSubmitting(true)
        try {
            await addReviewComment(projectId, newComment)
            setNewComment('')
            await loadComments()
        } catch (err) {
            console.error('Failed to add comment', err)
        }
        setSubmitting(false)
    }

    return (
        <div className="card" style={{ marginTop: 16 }}>
            <div className="card-header">
                <span className="card-title">Review Comments</span>
            </div>

            <div style={{ maxHeight: 400, overflowY: 'auto', marginBottom: 16 }}>
                {loading ? (
                    <div className="loading-spinner" />
                ) : comments.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>
                        No comments yet.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {comments.map(c => (
                            <div key={c.id} style={{ padding: 12, background: 'var(--bg-surface)', borderRadius: 8, borderLeft: c.user_role === 'admin' ? '3px solid var(--danger)' : c.user_role === 'reviewer' ? '3px solid var(--warning)' : '3px solid var(--success)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ fontWeight: 600 }}>{c.user_name}</span>
                                        <span className={`badge ${c.user_role === 'admin' ? 'badge-high' : c.user_role === 'reviewer' ? 'badge-medium' : 'badge-low'}`} style={{ fontSize: 10, padding: '2px 6px' }}>
                                            {c.user_role}
                                        </span>
                                    </div>
                                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{new Date(c.created_at).toLocaleString()}</span>
                                </div>
                                <div style={{ fontSize: 14, whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>{c.comment}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {canComment && (
                <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
                    <textarea
                        className="form-input"
                        placeholder="Add a review comment..."
                        value={newComment}
                        onChange={e => setNewComment(e.target.value)}
                        rows={3}
                        required
                        style={{ resize: 'vertical' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button type="submit" className="btn btn-primary" disabled={submitting || !newComment.trim()}>
                            {submitting ? 'Posting...' : 'Post Comment'}
                        </button>
                    </div>
                </form>
            )}
            {!canComment && (
                <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Only Reviewers and Admins can leave comments.
                </div>
            )}
        </div>
    )
}
