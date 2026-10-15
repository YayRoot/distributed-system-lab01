# distributed-system-lab01
here is the lab 01 "3-tier app"
-----------------------------------------------------------------------


# Calculator Web Application

A Flask-based calculator with persistent database logging.

## Features

- Basic arithmetic operations (+, -, ×, ÷)
- Calculation history
- Action logging (tracks all user interactions)
- Persistent SQLite database
- REST API endpoints

---

## Installation & Running

### Prerequisites

- Python 3.x installed
- pip package manager

### Setup and Run

1. **Navigate to project directory:**
```bash
   cd /path/to/project
```

2. **Install dependencies:**
```bash
   pip install -r requirements.txt
```

3. **Run the application:**
```bash
   python main.py
```

4. **Access the calculator:**
   - Open browser: `http://localhost:5000`

---

## Using the Application

### Main Calculator
http://localhost:5000

### View Action Logs
http://localhost:5000/api/logs

### View Statistics
http://localhost:5000/api/stats

### Clear History
```bash
curl -X DELETE http://localhost:5000/api/history
```

Or in browser console (F12):
```javascript
fetch('http://localhost:5000/api/history', { method: 'DELETE' })
```

---
## Screenshot
<img width="1919" height="1064" alt="Screenshot_20261015_161710" src="https://github.com/user-attachments/assets/25f28394-88d7-4b5b-9481-e01484ebf8cb" />


---

## Author

Made by Seraj
