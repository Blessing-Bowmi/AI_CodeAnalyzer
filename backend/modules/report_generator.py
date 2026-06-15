"""
Report Generator Module.
Generates PDF and JSON reports with code quality metrics.
"""

import json
import io
from datetime import datetime
from database import get_connection

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_json_report(project_id: int) -> dict:
    """Generate comprehensive JSON report."""
    conn = get_connection()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    files = conn.execute("SELECT id, file_name, file_path, language, loc FROM files WHERE project_id = ?", (project_id,)).fetchall()
    smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
    deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
    refactors = conn.execute("SELECT * FROM refactoring_history WHERE project_id = ?", (project_id,)).fetchall()
    suggestions = conn.execute("SELECT * FROM ai_suggestions WHERE project_id = ?", (project_id,)).fetchall()
    
    project_dict = dict(project) if project else {}
    
    # Smell summary
    smell_list = [dict(s) for s in smells]
    smell_by_type = {}
    smell_by_severity = {"high": 0, "medium": 0, "low": 0}
    for s in smell_list:
        stype = s["smell_type"]
        smell_by_type[stype] = smell_by_type.get(stype, 0) + 1
        smell_by_severity[s.get("severity", "low")] += 1
    
    # Refactor summary
    refactor_list = [dict(r) for r in refactors]
    refactor_by_type = {}
    refactor_by_status = {"suggested": 0, "applied": 0, "rejected": 0}
    for r in refactor_list:
        rtype = r["refactor_type"]
        refactor_by_type[rtype] = refactor_by_type.get(rtype, 0) + 1
        refactor_by_status[r.get("status", "suggested")] += 1
    
    report = {
        "report_date": datetime.now().isoformat(),
        "project": {
            "name": project_dict.get("project_name", ""),
            "upload_date": project_dict.get("upload_date", ""),
            "quality_score": project_dict.get("quality_score", 0),
            "total_files": len(files),
            "total_loc": sum(dict(f).get("loc", 0) for f in files),
        },
        "code_quality": {
            "score": project_dict.get("quality_score") or 0,
            "grade": _score_to_grade(project_dict.get("quality_score") or 0),
        },
        "smells": {
            "total": len(smell_list),
            "by_type": smell_by_type,
            "by_severity": smell_by_severity,
            "details": smell_list
        },
        "dependencies": {
            "total": len([dict(d) for d in deps]),
            "module_deps": len([d for d in deps if dict(d)["type"] == "module"]),
            "function_calls": len([d for d in deps if dict(d)["type"] == "function_call"]),
        },
        "refactoring": {
            "total": len(refactor_list),
            "by_type": refactor_by_type,
            "by_status": refactor_by_status,
            "history": refactor_list
        },
        "ai_suggestions": [dict(s) for s in suggestions],
        "files": [dict(f) for f in files]
    }
    
    # Store report
    conn.execute(
        "INSERT INTO reports (project_id, data_json) VALUES (?, ?)",
        (project_id, json.dumps(report))
    )
    conn.commit()
    conn.close()
    
    return report


def generate_pdf_report(project_id: int) -> bytes:
    """Generate PDF report."""
    report_data = generate_json_report(project_id)
    
    if not HAS_REPORTLAB:
        return json.dumps(report_data, indent=2).encode()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=22, textColor=colors.HexColor('#1a1a2e'), spaceAfter=20)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#16213e'), spaceBefore=15, spaceAfter=8)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, leading=14)
    
    elements = []
    
    # Title
    elements.append(Paragraph("Code Analysis Report", title_style))
    elements.append(Paragraph(f"Project: {report_data['project']['name']}", body_style))
    elements.append(Paragraph(f"Date: {report_data['report_date'][:10]}", body_style))
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", color=colors.HexColor('#e94560')))
    elements.append(Spacer(1, 15))
    
    # Quality Score
    score = report_data['code_quality']['score']
    grade = report_data['code_quality']['grade']
    elements.append(Paragraph("Code Quality Score", heading_style))
    score_color = '#27ae60' if score >= 70 else '#f39c12' if score >= 40 else '#e74c3c'
    elements.append(Paragraph(f"<font color='{score_color}' size='18'><b>{score}/100 ({grade})</b></font>", body_style))
    elements.append(Spacer(1, 15))
    
    # Project Overview
    elements.append(Paragraph("Project Overview", heading_style))
    overview_data = [
        ["Metric", "Value"],
        ["Total Files", str(report_data['project']['total_files'])],
        ["Total Lines of Code", str(report_data['project']['total_loc'])],
        ["Total Dependencies", str(report_data['dependencies']['total'])],
        ["Total Code Smells", str(report_data['smells']['total'])],
        ["Refactorings Suggested", str(report_data['refactoring']['total'])],
    ]
    overview_table = Table(overview_data, colWidths=[250, 200])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 15))
    
    # Code Smells
    elements.append(Paragraph("Code Smells Summary", heading_style))
    if report_data['smells']['by_type']:
        smell_data = [["Smell Type", "Count", "Max Severity"]]
        for stype, count in report_data['smells']['by_type'].items():
            smell_data.append([stype, str(count), "—"])
        smell_table = Table(smell_data, colWidths=[200, 100, 150])
        smell_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fff5f5'), colors.white]),
        ]))
        elements.append(smell_table)
    else:
        elements.append(Paragraph("No code smells detected. ✓", body_style))
    
    elements.append(Spacer(1, 15))
    
    # Refactoring History
    elements.append(Paragraph("Refactoring History", heading_style))
    if report_data['refactoring']['by_status']:
        status_data = [["Status", "Count"]]
        for status, count in report_data['refactoring']['by_status'].items():
            status_data.append([status.title(), str(count)])
        status_table = Table(status_data, colWidths=[200, 250])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(status_table)
    
    elements.append(Spacer(1, 20))
    
    # AI Suggestions
    elements.append(Paragraph("AI Recommendations", heading_style))
    for s in report_data.get('ai_suggestions', [])[:10]:
        suggestion_text = dict(s).get("suggestion", s) if isinstance(s, dict) else str(s)
        conf = dict(s).get("confidence_score", 0) if isinstance(s, dict) else 0
        elements.append(Paragraph(f"• {suggestion_text} (confidence: {conf:.0%})", body_style))
    
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", color=colors.HexColor('#e94560')))
    elements.append(Paragraph("<i>Generated by Intelligent Code Analyzer</i>", body_style))
    
    doc.build(elements)
    return buffer.getvalue()


def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    elif score >= 80: return "A"
    elif score >= 70: return "B"
    elif score >= 60: return "C"
    elif score >= 50: return "D"
    else: return "F"
