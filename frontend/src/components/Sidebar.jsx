import React, { useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

const commonNav = [
    {
        section: 'Main', items: [
            { to: '/', icon: '📊', label: 'Dashboard' },
            { to: '/upload', icon: '📁', label: 'Upload Project' },
        ]
    },
    {
        section: 'Analysis', items: [
            { to: '/dependencies/', icon: '🔗', label: 'Dependency Graph', needsId: true },
            { to: '/smells/', icon: '🔍', label: 'Code Smells', needsId: true },
            { to: '/refactor/', icon: '🔧', label: 'Refactor Suggestions', needsId: true },
            { to: '/preview/', icon: '👁️', label: 'Refactor Preview', needsId: true },
        ]
    },
    {
        section: 'Intelligence', items: [
            { to: '/ai/', icon: '🤖', label: 'AI Recommendations', needsId: true },
            { to: '/reports/', icon: '📄', label: 'Reports', needsId: true },
        ]
    },
]

const adminNav = [
    {
        section: 'Admin Panel', items: [
            { to: '/admin/dashboard', icon: '🛡️', label: 'Admin Dashboard' },
            { to: '/admin/users', icon: '👥', label: 'User Management' },
            { to: '/admin/analytics', icon: '📊', label: 'System Analytics' },
            { to: '/admin/activity', icon: '📋', label: 'Activity Log' },
        ]
    },
]

const roleBadgeColors = {
    admin: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
    reviewer: { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' },
    developer: { bg: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
}

export default function Sidebar({ user, onLogout }) {
    const location = useLocation()
    const match = location.pathname.match(/\/(dependencies|smells|refactor|preview|ai|reports)\/(\d+)/)
    const urlProjectId = match ? match[2] : null

    // Persist the last-used project ID so sidebar links always work
    useEffect(() => {
        if (urlProjectId) {
            localStorage.setItem('lastProjectId', urlProjectId)
        }
    }, [urlProjectId])

    const currentProjectId = urlProjectId || localStorage.getItem('lastProjectId')
    const isAdmin = user?.role === 'admin'

    const navItems = isAdmin ? [...adminNav, ...commonNav] : commonNav
    const badgeStyle = roleBadgeColors[user?.role] || roleBadgeColors.developer

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <h1>⚡ CodeAnalyzer</h1>
                <p>Intelligent Refactoring System</p>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((section) => {
                    const filteredItems = section.items.filter(item =>
                        !(item.to === '/upload' && user?.role !== 'developer')
                    )

                    if (filteredItems.length === 0) return null

                    return (
                        <div key={section.section}>
                            <div className="nav-section-label">{section.section}</div>
                            {filteredItems.map((item) => {
                                const to = item.needsId
                                    ? (currentProjectId ? `${item.to}${currentProjectId}` : '#')
                                    : item.to
                                const isActive = item.needsId
                                    ? location.pathname.startsWith(item.to)
                                    : location.pathname === item.to

                                return (
                                    <NavLink
                                        key={item.label}
                                        to={to}
                                        className={`nav-link ${isActive ? 'active' : ''} ${to === '#' ? 'disabled-link' : ''}`}
                                        onClick={(e) => {
                                            if (to === '#') {
                                                e.preventDefault();
                                                alert('Please select a project from the Dashboard first to view its analysis.');
                                            }
                                        }}
                                        style={to === '#' ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                                    >
                                        <span>{item.icon}</span>
                                        <span>{item.label}</span>
                                    </NavLink>
                                )
                            })}
                        </div>
                    )
                })}
            </nav>

            <div className="sidebar-footer">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 3 }}>{user?.name}</div>
                        <span style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: 50,
                            fontSize: 10,
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                            background: badgeStyle.bg,
                            color: badgeStyle.color,
                        }}>
                            {user?.role}
                        </span>
                    </div>
                    <button className="btn btn-ghost btn-sm" onClick={onLogout}>Logout</button>
                </div>
            </div>
        </aside>
    )
}
