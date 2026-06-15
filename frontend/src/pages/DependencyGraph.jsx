import React, { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { getDependencyGraph, getCircular } from '../services/api'
import * as d3 from 'd3'

export default function DependencyGraph() {
    const { id } = useParams()
    const [graph, setGraph] = useState(null)
    const [circular, setCircular] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const svgRef = useRef()

    useEffect(() => {
        const load = async () => {
            try {
                const [gRes, cRes] = await Promise.all([getDependencyGraph(id), getCircular(id)])
                setGraph(gRes.data)
                setCircular(cRes.data)
            } catch (err) {
                console.error(err)
                setError(true)
            }
            setLoading(false)
        }
        load()
    }, [id])

    useEffect(() => {
        if (!graph || !svgRef.current) return
        renderGraph()
    }, [graph])

    const renderGraph = () => {
        const svg = d3.select(svgRef.current)
        svg.selectAll('*').remove()

        const width = svgRef.current.clientWidth || 800
        const height = 500

        const g = svg.append('g')

        // Zoom
        svg.call(d3.zoom().scaleExtent([0.2, 4]).on('zoom', (e) => g.attr('transform', e.transform)))

        const nodes = graph.nodes.map(d => ({ ...d }))
        const links = graph.links.map(d => ({ ...d }))

        // Color scale
        const colorScale = d3.scaleOrdinal()
            .domain([1, 2, 3, 4, 5])
            .range(['#6366f1', '#f59e0b', '#22c55e', '#ec4899', '#64748b'])

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30))

        // Links
        const link = g.append('g').selectAll('line').data(links).join('line')
            .attr('stroke', d => d.is_circular ? '#ef4444' : '#2d2d44')
            .attr('stroke-width', d => d.is_circular ? 2.5 : 1)
            .attr('stroke-dasharray', d => d.is_circular ? '5,5' : 'none')
            .attr('opacity', 0.6)

        // Arrowheads
        svg.append('defs').append('marker')
            .attr('id', 'arrowhead').attr('viewBox', '0 -5 10 10')
            .attr('refX', 20).attr('refY', 0)
            .attr('markerWidth', 6).attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#2d2d44')

        link.attr('marker-end', 'url(#arrowhead)')

        // Nodes
        const node = g.append('g').selectAll('g').data(nodes).join('g')
            .call(d3.drag()
                .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
                .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
                .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
            )

        node.append('circle')
            .attr('r', d => d.size || 8)
            .attr('fill', d => d.is_circular ? '#ef4444' : colorScale(d.group))
            .attr('stroke', d => d.is_circular ? '#fca5a5' : 'transparent')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')

        node.append('text')
            .text(d => d.label)
            .attr('dx', 14).attr('dy', 4)
            .attr('font-size', '11px')
            .attr('fill', '#94a3b8')

        // Tooltip
        node.append('title').text(d => `${d.label}\nIn: ${d.in_degree} Out: ${d.out_degree}${d.is_circular ? '\n⚠️ Circular!' : ''}`)

        simulation.on('tick', () => {
            link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
            node.attr('transform', d => `translate(${d.x},${d.y})`)
        })
    }

    if (loading) return <div><div className="loading-spinner" /><div className="loading-text">Loading dependency graph...</div></div>

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
                <h2>Dependency Graph</h2>
                <p>Interactive visualization of module and function dependencies</p>
            </div>

            {graph?.metrics && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon blue">🔗</div>
                        <div><div className="stat-value">{graph.metrics.total_nodes}</div><div className="stat-label">Nodes</div></div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon purple">↗️</div>
                        <div><div className="stat-value">{graph.metrics.total_edges}</div><div className="stat-label">Edges</div></div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon red">🔄</div>
                        <div><div className="stat-value">{graph.metrics.circular_count}</div><div className="stat-label">Circular</div></div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon green">📏</div>
                        <div><div className="stat-value">{graph.metrics.avg_degree}</div><div className="stat-label">Avg Degree</div></div>
                    </div>
                </div>
            )}

            <div className="graph-container">
                <svg ref={svgRef} style={{ width: '100%', height: 500, background: 'var(--bg-card)' }} />
            </div>

            {circular && circular.cycles && circular.cycles.length > 0 && (
                <div className="card" style={{ marginTop: 20 }}>
                    <div className="card-header">
                        <span className="card-title">⚠️ Circular Dependencies</span>
                        <span className={`badge ${circular.health === 'critical' ? 'badge-high' : 'badge-medium'}`}>{circular.health}</span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>{circular.summary}</p>
                    {circular.resolutions?.map((r, i) => (
                        <div key={i} style={{ padding: 12, background: 'var(--bg-surface)', borderRadius: 8, marginBottom: 8 }}>
                            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>🔄 {r.cycle}</div>
                            {r.strategies?.map((s, j) => (
                                <div key={j} style={{ fontSize: 12, color: 'var(--text-secondary)', marginLeft: 16, marginBottom: 4 }}>
                                    • <strong>{s.name}:</strong> {s.description}
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
