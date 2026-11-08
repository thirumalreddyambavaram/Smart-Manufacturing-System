# YottaFlex Manufacturing Application

**A Manufacturing Planning, Production Scheduling and Resource Management System**

YottaFlex is a web-based manufacturing management application designed to help manufacturing teams manage production orders, machines, machine calendars, raw materials, inventory, routing operations, changeovers, labor shifts, tools and equipment, and production scheduling.

The application provides a centralized interface for monitoring manufacturing resources and managing production schedules with improved visibility into operational constraints.

---

## 1. Project Overview

YottaFlex provides the following modules:

| Module | Description |
|---|---|
| Dashboard | Manufacturing overview, production statistics and scheduling performance metrics |
| Production Schedule | View production schedules, machine allocations and operation timings |
| Production Orders | View and manage manufacturing orders |
| Products | Manage product and SKU information |
| Machines | View and manage manufacturing machines |
| Machine Calendars | Manage machine working schedules and shifts |
| Materials | Manage raw material information |
| Inventory Lots | Track material inventory lots and availability |
| Routings | Manage manufacturing routing information |
| Changeovers | Manage machine changeover information |
| Labor Shifts | Manage production shift information and worker availability |
| Tools & Equipment | Manage manufacturing tools and equipment |
| Exceptions & Anomalies | View scheduling exceptions and operational issues |

The application includes functionality for managing manufacturing data and generating production schedules.

---

## 2. Technology Stack

### Frontend
- React
- Vite
- JavaScript
- CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic

### Database
- MySQL

### Development Tools
- Visual Studio Code
- Git
- GitHub
- Node.js and npm
- Python

---

## 3. Project Structure

The main project structure is:

```text
YottaFlex-Manufacturing-Application/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── models/
│   │   ├── services/
│   │   ├── scheduling/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   └── migrations/
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/
├── docs/
├── scripts/
├── tests/
│
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

**Folder descriptions:**

- `backend/` – Backend application and API implementation.
- `backend/app/routers/` – API endpoints.
- `backend/app/models/` – Database models.
- `backend/app/services/` – Manufacturing business logic and services.
- `backend/app/scheduling/` – Production scheduling logic.
- `backend/migrations/` – Database migration files.
- `frontend/` – React-based user interface.
- `frontend/src/` – Frontend components and application pages.
- `data/` – Project data resources.
- `docs/` – Project documentation.
- `scripts/` – Utility and data-generation scripts.
- `tests/` – Backend and application tests.

---

## 4. Prerequisites

Install the following before running the application:

1. Python 3.11 or a compatible version.
2. Node.js and npm.
3. MySQL Server.
4. Git (optional, for cloning and version control).
5. Visual Studio Code (recommended).

Check your installations:

```powershell
python --version
node --version
npm --version
mysql --version
```

---

## 5. Download the Project

Clone the repository:

```bash
git clone https://github.com/thirumalreddyambavaram/YottaFlex-Manufacturing-Application.git
```

Open the downloaded project:

```bash
cd YottaFlex-Manufacturing-Application
```

Open the project folder in Visual Studio Code if desired.

---

## 6. Database Configuration

Make sure MySQL Server is running.

Create the database:

```sql
CREATE DATABASE yottaflex_manufacturing;
```

In the project root, create a file named `.env`.

Use the following configuration:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=yottaflex_manufacturing
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
```

Replace `YOUR_MYSQL_PASSWORD` with your own MySQL password.

**Important:** Never upload your `.env` file or database credentials to GitHub.

The `.env.example` file provides a configuration template.

---

## 7. Backend Setup

Open a terminal in the project root.

Create a Python virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Configure the database before starting the backend.

Start the FastAPI server:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

The backend will be available at:

**Backend API:**  
http://127.0.0.1:8000

**API Documentation:**  
http://127.0.0.1:8000/docs

---

## 8. Frontend Setup

Open a second terminal.

Navigate to the frontend directory:

```powershell
cd frontend
```

Install frontend dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Open the frontend application using the local URL displayed by Vite, normally:

http://localhost:5173

---

## 9. Running the Complete Application

The application requires both servers to run.

| Component | Local address |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://127.0.0.1:8000 |
| API Documentation | http://127.0.0.1:8000/docs |

**Terminal 1:** Run the backend.

**Terminal 2:** Run the frontend.

Keep both terminals running while using the application.

---

## 10. Testing

Backend tests are located in:

```text
tests/
```

To run the backend tests:

```powershell
python -m pytest tests/ -v
```

---

## 11. Security and Configuration

- Keep database passwords in the local `.env` file.
- Do not commit `.env` files.
- Do not upload virtual environments.
- Do not upload `node_modules`.
- Do not upload private database backups.
- Use `.env.example` as the configuration template.

---

## 12. Important Notes

- A running MySQL Server is required for database-backed functionality.
- The database must be configured before starting the backend.
- Database migrations and initial data setup should follow the project's migration and data-generation instructions.
- Do not run destructive database initialization or population commands against an existing database without taking a backup.
- The repository contains the application source code; a local database and its credentials are not automatically included.

---

## 13. Project Goal

The goal of YottaFlex is to provide a centralized manufacturing management platform that improves production visibility, resource utilization, scheduling coordination and operational decision-making.

**YottaFlex Manufacturing Application**  
Manufacturing Planning | Production Scheduling | Resource Management