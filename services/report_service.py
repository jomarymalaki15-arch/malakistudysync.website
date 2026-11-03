"""
StudySync Report Generation Service
Generates structured academic reports and exports to CSV and PDF format.
"""

import io
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from services.database import execute_query

def fetch_report_data(user_id, report_type='summary', subject_id=None, date_from=None, date_to=None):
    """Fetches filtered dataset for report generation."""
    query = """
        SELECT t.id, t.title, t.task_type, t.due_date, t.due_time, 
               t.priority, t.calculated_priority, t.status, t.completed_at, t.created_at,
               s.subject_code, s.subject_name
        FROM tasks t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE t.user_id = %s
    """
    params = [user_id]

    if report_type == 'completed':
        query += " AND t.status = 'Completed'"
    elif report_type == 'pending':
        query += " AND t.status IN ('Pending', 'In Progress')"
    elif report_type == 'overdue':
        query += " AND t.status = 'Overdue'"

    if subject_id:
        query += " AND t.subject_id = %s"
        params.append(subject_id)
    if date_from:
        query += " AND t.due_date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND t.due_date <= %s"
        params.append(date_to)

    query += " ORDER BY t.due_date ASC, t.due_time ASC"

    return execute_query(query, tuple(params), fetchall=True)

def generate_csv_report(user_info, tasks_data, report_title="StudySync Academic Report"):
    """Generates an in-memory CSV file content as a string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Metadata Header
    writer.writerow(["# " + report_title])
    writer.writerow(["# Student Name", user_info.get('full_name', 'Student')])
    writer.writerow(["# Student ID", user_info.get('student_id', 'N/A')])
    writer.writerow(["# Program", user_info.get('course_program', 'N/A')])
    writer.writerow(["# Generated At", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])

    # Table Column Headers
    writer.writerow([
        "Task ID", "Subject Code", "Subject Name", "Task Title", 
        "Task Type", "Due Date", "Due Time", "Priority", 
        "Calculated Priority", "Status", "Completed At"
    ])

    for row in tasks_data:
        writer.writerow([
            row['id'],
            row['subject_code'] or 'General',
            row['subject_name'] or 'N/A',
            row['title'],
            row['task_type'],
            str(row['due_date']),
            str(row['due_time']),
            row['priority'],
            row['calculated_priority'],
            row['status'],
            str(row['completed_at']) if row['completed_at'] else 'N/A'
        ])

    return output.getvalue()

def generate_pdf_report(user_info, tasks_data, report_title="StudySync Academic Report"):
    """Generates an in-memory PDF binary stream using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155'),
        leading=13
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    header_cell_style = ParagraphStyle(
        'HeaderCellText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    elements = []

    # Title & Subtitle
    elements.append(Paragraph(f"StudySync: {report_title}", title_style))
    elements.append(Paragraph("Intelligent Student Task and Deadline Management System", subtitle_style))

    # Student Metadata Card
    meta_text = f"""
    <b>Student:</b> {user_info.get('full_name', 'Student')} ({user_info.get('student_id', 'N/A')}) &nbsp;&nbsp;|&nbsp;&nbsp;
    <b>Program:</b> {user_info.get('course_program', 'N/A')} &nbsp;&nbsp;|&nbsp;&nbsp;
    <b>Generated:</b> {datetime.now().strftime('%b %d, %Y %I:%M %p')} &nbsp;&nbsp;|&nbsp;&nbsp;
    <b>Total Records:</b> {len(tasks_data)}
    """
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 14))

    # Table Data Construction
    table_data = [[
        Paragraph("ID", header_cell_style),
        Paragraph("Subject", header_cell_style),
        Paragraph("Title", header_cell_style),
        Paragraph("Type", header_cell_style),
        Paragraph("Due Date", header_cell_style),
        Paragraph("Priority", header_cell_style),
        Paragraph("Status", header_cell_style)
    ]]

    for t in tasks_data:
        status_val = t['status']
        prio_val = t['calculated_priority'] or t['priority']
        table_data.append([
            Paragraph(str(t['id']), cell_style),
            Paragraph(t['subject_code'] or 'General', cell_style),
            Paragraph(t['title'][:40] + ('...' if len(t['title']) > 40 else ''), cell_style),
            Paragraph(t['task_type'], cell_style),
            Paragraph(str(t['due_date']), cell_style),
            Paragraph(prio_val, cell_style),
            Paragraph(status_val, cell_style)
        ])

    if len(tasks_data) == 0:
        table_data.append([Paragraph("No records found matching criteria.", cell_style)] + [Paragraph("", cell_style)] * 6)

    # 540 pt available width for letter with 36 pt margins
    col_widths = [25, 60, 195, 65, 65, 65, 65]
    report_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))

    elements.append(report_table)
    elements.append(Spacer(1, 16))

    # Summary Footer
    comp_count = sum(1 for x in tasks_data if x['status'] == 'Completed')
    pend_count = sum(1 for x in tasks_data if x['status'] in ('Pending', 'In Progress'))
    over_count = sum(1 for x in tasks_data if x['status'] == 'Overdue')
    
    summary_text = f"<b>Summary:</b> Completed: {comp_count} | Pending/In Progress: {pend_count} | Overdue: {over_count}"
    elements.append(Paragraph(summary_text, meta_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
