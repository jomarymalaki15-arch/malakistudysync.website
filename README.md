# StudySync: Intelligent Student Task and Deadline Management System

StudySync is a modern, responsive, and full-featured web-based academic productivity platform engineered specifically for students and academic institutions. It organizes coursework, calculates explainable smart priorities, monitors academic workloads, prevents missed deadlines with intelligent reminders, and produces institutional-grade reports.

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask, Object-Oriented Architecture, Flask Blueprints
- **Database:** MySQL, XAMPP MySQL Server, phpMyAdmin, `mysql-connector-python`
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Jinja2 Templates, Bootstrap Icons, Chart.js, FullCalendar.js
- **Reporting Engine:** ReportLab (PDF generation) & CSV streaming

---

## 🚀 Key Features (All 15 Complete Features)

1. **Student Registration & Secure Authentication:**
   - Password hashing with Werkzeug (`scrypt`).
   - Session protection, student data isolation, and role-based access control (Student vs. Administrator).
   - Profile management and password updates.
2. **Task Management (Full CRUD):**
   - Create, edit, delete, view, and complete tasks.
   - Organized by Subject, Task Type (Assignment, Project, Quiz, Exam, Presentation, Other), Due Date, Due Time, and Priority.
3. **Real-Time Deadline Tracking:**
   - Categorized views: Due Today, Due Tomorrow, Upcoming (3-7+ days), Overdue, and Completed.
   - Dynamic countdown badges (e.g., *Due in 4h 30m*, *Overdue by 2d*).
4. **Smart Task Prioritization:**
   - Explainable rule-based algorithm: Critical, High, Medium, Low.
   - Factors in remaining hours to deadline, academic type weight (Exams & Projects carry higher impact), and student baseline urgency.
   - Displays a human-readable explanation for every calculated priority.
5. **Subject Organization:**
   - Add, edit, and delete academic subjects.
   - Custom color tags and badges for visual differentiation across calendars and boards.
6. **Smart Reminders & Notification Center:**
   - Automatic background evaluation for tasks due today, tomorrow, approaching exams, and overdue items.
   - Stored in MySQL `notifications` and `reminders` tables with 24-hour duplicate suppression.
   - Topbar notification bell with unread badge and dropdown preview.
7. **Interactive Calendar View:**
   - Integrated FullCalendar.js supporting Month, Week, Day, and Agenda views.
   - Color-coded events reflecting subject colors and completion states.
   - Click date to schedule a new task with pre-filled date; click event to preview details and toggle status.
8. **Task Status Tracking (Kanban Board):**
   - Statuses: Pending, In Progress, Overdue, and Completed.
   - Automated overdue state transition when deadline elapses.
   - Dedicated Kanban board with quick status movement menus.
9. **Academic Workload Monitoring:**
   - Dynamic stress index assessment (Light, Moderate, Heavy, Overloaded).
   - Tasks due this week, upcoming examination alerts, and course distribution bars.
10. **Progress Dashboard:**
    - Visual metrics: total tasks, completed, pending, and overdue.
    - Overall completion rate percentage bar and subject mastery progress bars.
11. **Task Search & Advanced Filtering:**
    - Search by keyword across titles, rubrics, and descriptions.
    - Multi-criteria filters: Subject, Status, Priority, Type, and Sort order.
12. **Intelligent Study Recommendations:**
    - Deterministic, rule-based recommendation engine (no paid external APIs required).
    - Detects same-day deadline clusters, subject backlogs, and approaching exams.
13. **Completion Statistics:**
    - Velocity breakdown: daily, weekly, and monthly completion counts.
    - On-time submission punctuality percentage.
    - Subject-based velocity and completion tables.
14. **Administrator Control Center:**
    - Accessible strictly to users with the `admin` role.
    - Registered student directory with account activation/deactivation toggles.
    - System-wide aggregate KPI cards.
    - System audit logs and activity tracking.
    - Privacy enforcement: students' private task descriptions are isolated and protected.
15. **Reports & Exports:**
    - Task Summary, Completed, Pending, and Overdue reports with date and course filtering.
    - One-click export to official **PDF** (via ReportLab) and standard **CSV**.

---

## 📂 Project Structure

```text
StudySync/
│
├── app.py                     # Main application factory and server entry point
├── config.py                  # Environment-based configuration settings
├── requirements.txt           # Python package dependencies
├── .env.example               # Template environment configuration
├── .env                       # Local environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # Comprehensive setup and user guide
│
├── database/
│   ├── studysync_db.sql       # Complete MySQL database export (phpMyAdmin ready)
│   └── init_db.py             # CLI database migration script
│
├── models/
│   ├── __init__.py
│   ├── user.py                # User entity, authentication & admin methods
│   ├── subject.py             # Academic course subjects
│   ├── task.py                # Tasks, deadline logic, and status state machine
│   └── notification.py        # Alerts and notifications
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Register, login, logout, profile & settings
│   ├── dashboard.py           # Dashboard overview and Chart.js APIs
│   ├── tasks.py               # CRUD, deadlines, priority, workload, progress, search
│   ├── subjects.py            # Subject management
│   ├── calendar.py            # FullCalendar views and event feed API
│   ├── reminders.py           # Notifications center and reminder queue
│   ├── reports.py             # Filtered reports, CSV and PDF generation
│   └── admin.py               # Administrator console and audit logs
│
├── services/
│   ├── __init__.py
│   ├── database.py            # Connection pooling, query execution, transactions
│   ├── priority_service.py    # Explainable smart priority heuristic engine
│   ├── reminder_service.py    # Duplicate-preventing reminder triggers
│   └── report_service.py      # PDF (ReportLab) and CSV formatters
│
├── templates/
│   ├── base.html              # Core Figma-style layout with topbar and 15-item sidebar
│   ├── login.html             # Secure user and admin sign-in
│   ├── register.html          # Student self-registration
│   ├── profile.html           # User profile and password updates
│   ├── settings.html          # Reminder lead times and visual settings
│   ├── dashboard.html         # 6 KPI cards, progress bar, Chart.js charts
│   ├── tasks.html             # Task management table with filter pills
│   ├── task_form.html         # Add/edit task form with live priority fields
│   ├── deadlines.html         # Tabbed deadline tracking (Today, Tomorrow, Upcoming, Overdue)
│   ├── priority_tasks.html    # Tasks categorized into Critical, High, Medium, Low
│   ├── subjects.html          # Subject cards with color palettes
│   ├── calendar.html          # Interactive FullCalendar interface
│   ├── task_status.html       # 4-column Kanban board
│   ├── workload.html          # Academic workload monitor and exam alerts
│   ├── progress.html          # Academic progress dashboard
│   ├── search.html            # Multi-criteria search and filter interface
│   ├── recommendations.html   # Rule-based study recommendations
│   ├── statistics.html        # Detailed completion velocity & on-time stats
│   ├── reports.html           # Filtered report generator with live preview
│   └── admin.html             # Administrator dashboard, user controls, and audit logs
│
├── static/
│   ├── css/
│   │   └── style.css          # Figma design system (Navy #0F172A, Blue #2563EB, Purple #7C3AED)
│   └── js/
│       └── script.js          # Chart.js initialization, tooltips, and modal bindings
│
└── tests/
    ├── __init__.py
    ├── test_auth.py           # Auth, sessions, and password security tests
    ├── test_tasks.py          # Prioritization, isolation, and task tests
    └── test_features.py       # Subject CRUD, calendar API, reports, and admin tests
```

---

## ⚙️ Installation and Execution (Windows + VS Code + XAMPP)

### Step 1: Prerequisites
Ensure you have the following installed on Windows:
- **Python 3.10+** (Python 3.14 recommended)
- **XAMPP Control Panel** (with Apache and MySQL)
- **Visual Studio Code** (or any modern code editor)
- **Web Browser** (Google Chrome, Microsoft Edge, or Firefox)

### Step 2: Start XAMPP MySQL
1. Open the **XAMPP Control Panel**.
2. Click **Start** on **MySQL** (and optionally **Apache** if using phpMyAdmin).
3. Verify that MySQL is running on port `3306`.

### Step 3: Import the Database
You can import the database using either **phpMyAdmin** or the built-in automated script:

#### Option A: Using phpMyAdmin
1. Open your browser and go to `http://localhost/phpmyadmin`.
2. Click the **Import** tab in top navigation.
3. Choose the file: `database/studysync_db.sql`.
4. Click **Import** at the bottom.
5. Confirm that the `studysync_db` database and all 8 tables are created.

#### Option B: Automated Python Script (Recommended)
Open a terminal in the project directory and run:
```bash
python database/init_db.py
```
This automatically connects to MySQL, creates the database, initializes all 8 tables, and seeds the sample data.

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Default configuration for XAMPP:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=studysync_db
SECRET_KEY=studysync-secure-secret-key-2026-prod
```

### Step 5: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 6: Run the Unit & Integration Tests
Verify system integrity before launch:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
*(All 16 test cases should pass with `OK`.)*

### Step 7: Start the StudySync Application
```bash
python app.py
```

### Step 8: Open in Browser
Visit:
```text
http://127.0.0.1:5000
```

---

## 🔑 Pre-Configured Test Accounts

| Role | Identifier / Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Student** | `student@studysync.edu` (or `STU-2026-001`) | `StudentPassword123!` | Complete student productivity suite, personal subjects, tasks, calendar, workload, reports |
| **Admin** | `admin@studysync.edu` (or `ADM-001`) | `AdminPassword123!` | System-wide statistics, user activation/deactivation, audit logs, system maintenance |

---

## 🔒 Security & Data Isolation
- **Student Data Isolation:** Every query verifying tasks, subjects, reminders, and history enforces `WHERE user_id = session['user_id']`.
- **SQL Injection Prevention:** 100% of database queries use parameterized execution (`%s` placeholders).
- **Password Protection:** Stored using cryptographic salt and hash via Werkzeug's `generate_password_hash`.
- **Administrative Privacy:** Administrator accounts inspect platform metrics, activity logs, and account statuses, without viewing private student task notes.
