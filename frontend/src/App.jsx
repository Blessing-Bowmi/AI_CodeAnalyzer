import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import DependencyGraph from './pages/DependencyGraph'
import SmellViewer from './pages/SmellViewer'
import RefactorSuggestions from './pages/RefactorSuggestions'
import RefactorPreview from './pages/RefactorPreview'
import Reports from './pages/Reports'
import AIRecommendations from './pages/AIRecommendations'
import AdminDashboard from './pages/AdminDashboard'
import UserManagement from './pages/UserManagement'
import SystemAnalytics from './pages/SystemAnalytics'
import AdminActivity from './pages/AdminActivity'

function App() {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('token')
        const userData = localStorage.getItem('user')
        if (token && userData) {
            setUser(JSON.parse(userData))
        }
        setLoading(false)
    }, [])

    const handleLogin = (userData, token) => {
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(userData))
        setUser(userData)
    }

    const handleLogout = () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setUser(null)
    }

    if (loading) return <div className="loading-spinner" style={{ marginTop: '45vh' }} />

    if (!user) {
        return (
            <Routes>
                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route path="/register" element={<Register onLogin={handleLogin} />} />
                <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
        )
    }

    const isAdmin = user.role === 'admin'

    return (
        <div className="app-layout">
            <Sidebar user={user} onLogout={handleLogout} />
            <main className="main-content">
                <Routes>
                    {/* Common routes */}
                    <Route path="/" element={isAdmin ? <AdminDashboard /> : <Dashboard user={user} />} />
                    <Route path="/upload" element={user.role === 'developer' ? <Upload /> : <Navigate to="/" />} />
                    <Route path="/dependencies/:id" element={<DependencyGraph />} />
                    <Route path="/smells/:id" element={<SmellViewer />} />
                    <Route path="/refactor/:id" element={<RefactorSuggestions />} />
                    <Route path="/preview/:id" element={<RefactorPreview />} />
                    <Route path="/ai/:id" element={<AIRecommendations />} />
                    <Route path="/reports/:id" element={<Reports user={user} />} />

                    {/* Admin-only routes */}
                    {isAdmin && (
                        <>
                            <Route path="/admin/dashboard" element={<AdminDashboard />} />
                            <Route path="/admin/users" element={<UserManagement />} />
                            <Route path="/admin/analytics" element={<SystemAnalytics />} />
                            <Route path="/admin/activity" element={<AdminActivity />} />
                        </>
                    )}

                    <Route path="*" element={<Navigate to="/" />} />
                </Routes>
            </main>
        </div>
    )
}

export default App
