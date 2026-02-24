from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


def calculate_grade(percentage):
    if percentage >= 90:
        return 'A'
    elif percentage >= 80:
        return 'B'
    elif percentage >= 70:
        return 'C'
    elif percentage >= 60:
        return 'D'
    else:
        return 'Fail'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        # Handle preflight request
        return '', 200

    data = request.get_json()
    students = data['students']

    analyzed_students = []
    total_percentages = []

    for student in students:
        name = student['name']
        marks = student['marks']

        # Validate marks
        if any(mark > 100 or mark < 0 for mark in marks):
            return jsonify({'error': f'Invalid marks for {name}'}), 400

        total = sum(marks)
        percentage = (total / 500) * 100
        grade = calculate_grade(percentage)

        analyzed_students.append({
            'name': name,
            'marks': marks,
            'total': total,
            'percentage': round(percentage, 2),
            'grade': grade
        })

        total_percentages.append(percentage)

    # Find topper
    topper = max(analyzed_students, key=lambda x: x['percentage'])

    # Calculate class average
    class_average = round(sum(total_percentages) / len(total_percentages), 2) if total_percentages else 0

    return jsonify({
        'students': analyzed_students,
        'topper': topper,
        'class_average': class_average
    })


@app.route('/generate_pdf', methods=['POST', 'OPTIONS'])
def generate_pdf():
    if request.method == 'OPTIONS':
        # Handle preflight request
        return '', 200

    data = request.get_json()
    students = data['students']
    topper = data['topper']
    class_average = data['class_average']

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("Student Performance Report", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Date
    date = Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal'])
    elements.append(date)
    elements.append(Spacer(1, 12))

    # Table data
    table_data = [['Name', 'Sub1', 'Sub2', 'Sub3', 'Sub4', 'Sub5', 'Total', 'Percentage', 'Grade']]
    for student in students:
        row = [student['name']] + student['marks'] + [student['total'], f"{student['percentage']}%", student['grade']]
        table_data.append(row)

    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Topper and Average
    topper_para = Paragraph(f"Topper: {topper['name']} ({topper['percentage']}%)", styles['Normal'])
    elements.append(topper_para)

    average_para = Paragraph(f"Class Average: {class_average}%", styles['Normal'])
    elements.append(average_para)

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='student_report.pdf', mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)