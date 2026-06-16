# Face Recognition Attendance System 2.0

A full-stack attendance management system that uses face recognition to mark student attendance automatically. Built with Python, Flask, OpenCV, SQLite/MySQL-ready schema, role-based login, dashboard, reports, CSV export, and optional email notifications.

## Features

- Admin, faculty, and student login roles
- Student registration
- Webcam-based face sample capture
- OpenCV LBPH face recognition model training
- Live face recognition attendance marking
- One attendance entry per student per day
- Dashboard with total students and attendance count
- Date-wise attendance reports
- CSV export
- Optional email notification after attendance is marked
- SQLite database by default
- MySQL schema included in `database.sql`

## Tech Stack

- Python
- Flask
- OpenCV
- SQLite / MySQL schema
- HTML
- CSS
- Pandas

## Project Structure

```text
Face-Recognition-Attendance-System/
├── app.py
├── requirements.txt
├── database.sql
├── README.md
├── utils/
│   ├── database.py
│   ├── face_utils.py
│   └── email_alert.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html
│   ├── add_student.html
│   ├── recognize.html
│   └── reports.html
├── static/css/style.css
├── dataset/student_faces/
└── encodings/
```

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Flask app

```bash
python app.py
```

Open browser:

```text
http://127.0.0.1:5000
```

## Default Login

```text
Username: admin
Password: admin123
```

## Usage Flow

1. Login as admin.
2. Add a student.
3. The webcam opens automatically to capture face samples.
4. Click **Train Model**.
5. Click **Recognize** to start live face recognition.
6. Attendance will be marked automatically.
7. Go to **Reports** to view or export attendance.

## Optional Email Setup

Create a `.env` file or set these environment variables:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

For Gmail, use an App Password instead of your normal password.

## GitHub Repository Description

```text
A Python Flask and OpenCV based Face Recognition Attendance System with role-based login, dashboard, reports, CSV export, and email notifications.
```

## Future Enhancements

- MySQL integration in app runtime
- Student-wise monthly analytics charts
- Low attendance alert system
- REST API for mobile app integration
- Deployment using Docker

## Author

Developed as a portfolio project for Python, Flask, OpenCV, SQL, and backend development practice.
