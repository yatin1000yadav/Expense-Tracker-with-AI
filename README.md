# 💸 Expense Tracker — AI-powered Personal Finance Dashboard  

A **privacy-first, AI-assisted expense tracker** built with **Streamlit**, **Google Sheets**, and **Pandas**.  
It helps you log income & expenses, visualize financial trends, and receive **AI storytelling insights** about your spending habits — all in a single, secure, and lightweight app.

---

## 🎥 Demo Video
▶️ Watch full walkthrough here: [YouTube Demo](https://youtu.be/1N9xm3wrHAY)  

---

## ✨ Features
- 🔐 **Password-protected login** (bcrypt hashed)  
- ☁️ **Google Sheets as backend** (yearly tabs like `test-2024`, `test-2025`)  
- 📊 **Visual Insights**: Weekly, Monthly & Yearly summaries with charts and tables  
- 🧠 **AI-powered Storytelling & Financial Health Score**  
  - Explains your top spending patterns in **plain English**  
  - Suggests where to save & cut back  
- 🗂️ **Automatic yearly sheet creation** (new tab every January)  
- 🔎 **Category & note-based deep analysis** (not just numbers!)  
- 🚫 **No SMS scraping** → Full privacy + cash transactions included  

---

## 🛠️ Tech Stack
- **Frontend/UI:** Streamlit  
- **Data Handling:** Pandas  
- **Database:** Google Sheets (via gspread + oauth2client)  
- **Visualizations:** Altair, Plotly, Matplotlib  
- **Security:** bcrypt (password hashing)  
- **Storage:** Excel (openpyxl for dummy/test data)  


---

## ⚙️ Setup & Installation

1️⃣ **Clone Repo**
```bash
git clone https://github.com/projectmaker-official/AI-Expense-Tracker.git
cd ExpenseTracker
```
2️⃣ **Install Dependencies**
```
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```
3️⃣ **Configure Google Sheets**
 - Create Google Cloud project → enable Google Sheets API
 - Create service account → download JSON key → rename to birthday.json
 - Place file in config/birthday.json
 - Share your Google Sheet with the service account email (Editor access)

4️⃣ **Setup Password**
  Create a bcrypt-hashed password:
   ```
  import bcrypt, json
  pw = b"your_password_here"
  hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
  with open('config/auth.json','w') as f:
      json.dump({"hashed_password": hashed}, f)
   ```
5️⃣ **Run the App**
```
streamlit run main.py
```
❓**Why Not Use Mobile SMS Data?**

### This project does not scrape SMS messages for a few key reasons:

 - 💵 Cash transactions don’t generate SMS → data would be incomplete
 - 📝 SMS rarely includes categories or notes, which are crucial for deep analysis
 - ⚠️ SMS parsing differs across banks → error-prone and inconsistent
 - 🔒 Accessing SMS requires privacy-intrusive permissions
 - ✅ Manual entry ensures clean, context-rich data for AI insights

🧠 **AI Insights**

### Our AI storytelling feature provides:

 - 📈 Key expense trends
 - 💡 Saving opportunities
 - ⚠️ Overspending warnings
 - 🎯 Expense concentration highlights
 - 🧩 Contextual suggestions based on your notes

### The goal: explain your financial health in human terms, not just numbers.

📁 **Sample Data**

 - sample_data/expense_dummy_data.xlsx provided for testing.
 - Includes realistic dummy transactions (2024 → Sept 2025).
 - Format: DD-MM-YYYY, with categories, debit/credit details, and notes.

🔐 **Security Notes**

 - Never commit your personal birthday.json or auth.json.
 - Store credentials locally only.
 - Passwords are securely hashed (bcrypt).

🤝 **Contributing**
 - Want to improve? Fork the repo, raise an issue, or submit a PR 🚀
 - Just remember — do not upload personal credentials.

🏆 **Credits**

 - Built with ❤️ using Streamlit + Google Sheets + AI-powered insights
 - Created to make expense tracking simple, secure, and insightful.
