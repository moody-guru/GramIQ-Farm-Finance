# GramIQ Farm Finance Reporting System

## 📋 Overview
This is a full-stack web application developed for the **GramIQ Backend Developer Intern Assessment**. The system allows farmers to input crop details, expenses, and income to automatically generate a comprehensive financial PDF report. It includes features for calculating net profit, cost of cultivation per acre, and visualizing financial data through charts.

**Key Features:**
* **Dynamic PDF Generation:** Creates professional reports with the GramIQ branding.
* **Financial Analytics:** Auto-calculates Total Income, Expense, Profit/Loss, and Cost per Acre.
* **Data Persistence:** Uses SQLite to save report history, allowing users to view or edit past reports.
* **Interactive Charts:** Embeds Matplotlib charts directly into the PDF.
* **Responsive UI:** Mobile-friendly interface built with Tailwind CSS.

---

## 🛠️ Tech Stack
* **Backend:** Python (FastAPI)
* **PDF Engine:** ReportLab
* **Data Visualization:** Matplotlib
* **Database:** SQLite (Built-in)
* **Frontend:** HTML5, JavaScript, Tailwind CSS (via CDN)

---

## ⚙️ Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Clone the Repository
```bash
git clone <YOUR_GITHUB_REPO_LINK_HERE>
cd <YOUR_PROJECT_FOLDER_NAME>
