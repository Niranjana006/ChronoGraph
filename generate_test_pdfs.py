import os
from fpdf import FPDF

docs = {
    "test_alpha_1.pdf": "Project Alpha launch date is officially Q3 2024. All marketing materials should align with this release schedule.",
    "test_alpha_2.pdf": "Due to recent delays, Project Alpha is scheduled for Q4 2024. Please update the launch timeline.",
    
    "test_ceo_1.pdf": "John Doe has been appointed as the CEO, serving a term from January 2022 to December 2025.",
    "test_ceo_2.pdf": "Jane Smith is taking over as the CEO effective June 2024, with a contract running until December 2026.",
    
    "test_server_1.pdf": "The standard server RAM allocation for production environments is exactly 16GB.",
    "test_server_2.pdf": "According to the new infrastructure requirements, all standard servers must be configured with 32GB RAM."
}

for filename, content in docs.items():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=content)
    pdf.output(filename)
    print(f"Created {filename}")
