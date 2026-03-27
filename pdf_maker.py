from fpdf import FPDF

def generate_report(rpm, diag_type, probabilities, recommendation, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="AI-Garage Diagnostic Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Estimated RPM: {int(rpm)}", ln=True)
    pdf.cell(200, 10, txt=f"Diagnosis: {diag_type.replace('_', ' ').upper()}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Expert Recommendation:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=recommendation) # Добавили в PDF
    
    pdf.ln(10)
    pdf.output(output_path)