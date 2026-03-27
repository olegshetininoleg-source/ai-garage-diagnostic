from fpdf import FPDF

def generate_report(rpm, diag_type, probabilities, output_path):
    pdf = FPDF()
    pdf.add_page()
    
    # Заголовок
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="AI-Garage Diagnostic Report", ln=True, align='C')
    pdf.ln(10)
    
    # Основные данные
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Estimated RPM: {int(rpm)}", ln=True)
    pdf.cell(200, 10, txt=f"Primary Diagnosis: {diag_type}", ln=True)
    pdf.ln(10)
    
    # Детализация
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Confidence Matrix:", ln=True)
    pdf.set_font("Arial", size=12)
    for issue, prob in probabilities.items():
        pdf.cell(200, 10, txt=f"- {issue}: {prob}%", ln=True)
        
    # Сохранение
    pdf.output(output_path)