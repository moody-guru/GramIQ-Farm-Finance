import io
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = FastAPI()

# --- SETUP DIRECTORIES ---
os.makedirs("reports", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- DATABASE SETUP (SQLite) ---
DB_NAME = "farm_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  farmer_name TEXT, 
                  crop_name TEXT, 
                  filename TEXT, 
                  json_data TEXT,
                  created_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- DATA MODELS ---
class ExpenseItem(BaseModel):
    category: str
    amount: float
    date: str
    description: Optional[str] = ""

class IncomeItem(BaseModel):
    category: str
    amount: float
    date: str
    description: Optional[str] = ""

class FarmData(BaseModel):
    farmer_name: str
    crop_name: str
    season: str
    total_acres: float
    sowing_date: str
    harvest_date: str
    location: str
    total_production: float
    expenses: List[ExpenseItem]
    incomes: List[IncomeItem]

# --- PDF GENERATION ---
def generate_charts(income_total, expense_total):
    fig, ax = plt.subplots(figsize=(4, 3))
    labels = ['Income', 'Expenses']
    sizes = [income_total, expense_total]
    colors_list = ['#4CAF50', '#FF5722'] 
    
    if sum(sizes) == 0: sizes = [1, 1]
    
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_list, startangle=90)
    ax.axis('equal')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def create_and_save_pdf(data: FarmData):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = data.farmer_name.replace(" ", "_")
    filename = f"{clean_name}_{data.crop_name}_{timestamp}.pdf"
    filepath = os.path.join("reports", filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # LOGO
    try:
        logo = RLImage("static/logo.png", width=1.5*inch, height=0.6*inch)
        logo.hAlign = 'LEFT'
        elements.append(logo)
    except: pass
    elements.append(Spacer(1, 0.2*inch))

    # HEADER
    # --- FIX 1: Use colors.HexColor instead of colors.hexval ---
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.HexColor("#4A148C"))
    elements.append(Paragraph(f"Farm Finance Report: {data.crop_name}", title_style))
    elements.append(Paragraph(f"<b>Farmer:</b> {data.farmer_name} | <b>Location:</b> {data.location}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # TABLES & CHARTS LOGIC
    total_inc = sum(i.amount for i in data.incomes)
    total_exp = sum(e.amount for e in data.expenses)
    profit = total_inc - total_exp
    cost_per_acre = total_exp / data.total_acres if data.total_acres > 0 else 0

    summary_data = [
        ["Financial Metrics", "Value"],
        ["Total Income", f"INR {total_inc:,.2f}"],
        ["Total Expense", f"INR {total_exp:,.2f}"],
        ["Net Profit/Loss", f"INR {profit:,.2f}"],
        ["Cost of Cultivation / Acre", f"INR {cost_per_acre:,.2f}"]
    ]
    t_sum = Table(summary_data, colWidths=[250, 150])
    t_sum.setStyle(TableStyle([
        # --- FIX 2: Use colors.HexColor ---
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#6A1B9A")),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_sum)
    elements.append(Spacer(1, 0.2*inch))

    chart_buf = generate_charts(total_inc, total_exp)
    elements.append(RLImage(chart_buf, width=250, height=180))
    elements.append(Spacer(1, 0.2*inch))

    # TABLE STYLES
    table_style = TableStyle([
        # --- FIX 3: Use colors.HexColor ---
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E1BEE7")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])

    # Expenses
    elements.append(Paragraph("Expense Breakdown", styles['Heading3']))
    if data.expenses:
        e_data = [["Category", "Date", "Amount"]] + [[e.category, e.date, f"{e.amount}"] for e in data.expenses]
        t_exp = Table(e_data, colWidths=[150, 100, 100])
        t_exp.setStyle(table_style)
        elements.append(t_exp)
    elements.append(Spacer(1, 0.2*inch))

    # Income
    elements.append(Paragraph("Income Breakdown", styles['Heading3']))
    if data.incomes:
        i_data = [["Category", "Date", "Amount"]] + [[i.category, i.date, f"{i.amount}"] for i in data.incomes]
        t_inc = Table(i_data, colWidths=[150, 100, 100])
        t_inc.setStyle(table_style)
        elements.append(t_inc)

    doc.build(elements)
    return filename

# --- ROUTES ---

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate")
def generate_report_endpoint(data: FarmData):
    filename = create_and_save_pdf(data)
    
    # Store JSON data in DB
    json_str = json.dumps(data.dict())
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO reports (farmer_name, crop_name, filename, json_data, created_at) VALUES (?, ?, ?, ?, ?)",
              (data.farmer_name, data.crop_name, filename, json_str, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    
    return {"status": "success", "filename": filename}

@app.get("/api/reports")
def get_reports():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM reports ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

@app.get("/reports/{filename}")
def download_report(filename: str):
    path = os.path.join("reports", filename)
    if os.path.exists(path):
        return FileResponse(path, media_type='application/pdf', filename=filename)
    return JSONResponse(status_code=404, content={"message": "File not found"})