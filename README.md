# Face Recognition Attendance System 2.0

A full-stack attendance management system built using **Python, Flask, OpenCV and SQLite/MySQL**. It allows admins to register students with face images, mark attendance using face recognition, view attendance dashboards, filter reports, export CSV files and send email notifications.

## Features

- Admin login system
- Student registration with face image
- Face detection using OpenCV Haar Cascade
- Face-based attendance marking
- Dashboard with attendance statistics
- Date-wise attendance reports
- CSV export
- Email notification support using SMTP
- SQLite by default, MySQL schema included
- Clean Flask folder structure

## Tech Stack

- Python
- Flask
- OpenCV
- SQLite / MySQL
- HTML
- CSS
- JavaScript

## Folder Structure

```text
Face-Recognition-Attendance-System-Complete/
├── app.py
├── requirements.txt
├── database.sql
├── README.md
├── templates/
├── static/
├── utils/
├── dataset/
├── encodings/
└── exports/
```

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/your-username/face-recognition-attendance-system.git
cd face-recognition-attendance-system
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Run the Flask app

```bash
python app.py
```

Open in browser:

```text
http://127.0.0.1:5000
```

## Default Login

```text
Username: admin
Password: admin123
```

## Email Notification Setup

Create a `.env` file or set environment variables:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

Email sending is optional. The app still works without SMTP configuration.

## MySQL Support

The app uses SQLite by default for easy testing. A MySQL schema is provided in `database.sql`.

## Future Enhancements

- Live webcam attendance capture
- Role-based faculty/student dashboards
- Monthly analytics charts
- Low attendance alerts
- Docker deployment
- Cloud database integration
