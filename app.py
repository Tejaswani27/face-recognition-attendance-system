from datetime import datetime, date
from functools import wraps
from pathlib import Path

import cv2
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_file
from werkzeug.security import check_password_hash, generate_password_hash

from utils.database import init_db, get_connection
from utils.face_utils import capture_student_faces, train_model, load_recognizer, _detector
from utils.email_alert import send_email

app = Flask(__name__)
app.secret_key = 'change-this-secret-key'
init_db()


def login_required(roles=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if roles and session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_connection()
        user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required()
def dashboard():
    conn = get_connection()
    total_students = conn.execute('SELECT COUNT(*) c FROM students').fetchone()['c']
    today_count = conn.execute('SELECT COUNT(*) c FROM attendance WHERE attendance_date=?', (date.today().isoformat(),)).fetchone()['c']
    total_attendance = conn.execute('SELECT COUNT(*) c FROM attendance').fetchone()['c']
    rows = conn.execute('''
        SELECT s.name, s.roll_no, a.attendance_date, a.attendance_time
        FROM attendance a JOIN students s ON s.id=a.student_id
        ORDER BY a.id DESC LIMIT 8
    ''').fetchall()
    conn.close()
    return render_template('dashboard.html', total_students=total_students, today_count=today_count,
                           total_attendance=total_attendance, recent=rows)


@app.route('/students')
@login_required(['admin', 'faculty'])
def students():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('students.html', students=rows)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required(['admin', 'faculty'])
def add_student():
    if request.method == 'POST':
        data = (request.form['roll_no'].strip(), request.form['name'].strip(), request.form.get('email','').strip(),
                request.form.get('department','').strip(), request.form.get('year','').strip())
        conn = get_connection()
        try:
            cur = conn.execute('INSERT INTO students(roll_no, name, email, department, year) VALUES (?, ?, ?, ?, ?)', data)
            student_id = cur.lastrowid
            conn.execute('INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)',
                         (data[0], generate_password_hash('student123'), 'student'))
            conn.commit()
            flash(f'Student added. Default student login: username={data[0]}, password=student123', 'success')
            return redirect(url_for('capture_faces', student_id=student_id))
        except Exception as e:
            flash(f'Could not add student: {e}', 'danger')
        finally:
            conn.close()
    return render_template('add_student.html')


@app.route('/capture/<int:student_id>')
@login_required(['admin', 'faculty'])
def capture_faces(student_id):
    try:
        count = capture_student_faces(student_id)
        flash(f'Captured {count} face samples successfully.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('students'))


@app.route('/train')
@login_required(['admin', 'faculty'])
def train():
    try:
        total = train_model()
        flash(f'Model trained successfully for {total} students.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('dashboard'))


def mark_attendance(student_id: int):
    now = datetime.now()
    conn = get_connection()
    student = conn.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
    if student:
        conn.execute('''
            INSERT OR IGNORE INTO attendance(student_id, attendance_date, attendance_time, status)
            VALUES (?, ?, ?, ?)
        ''', (student_id, now.date().isoformat(), now.time().strftime('%H:%M:%S'), 'Present'))
        conn.commit()
        if student['email']:
            send_email(student['email'], 'Attendance Marked',
                       f'Hi {student["name"]}, your attendance was marked on {now.strftime("%d-%m-%Y %H:%M")}.')
    conn.close()


@app.route('/recognize')
@login_required(['admin', 'faculty'])
def recognize():
    return render_template('recognize.html')


@app.route('/video_feed')
@login_required(['admin', 'faculty'])
def video_feed():
    recognizer = load_recognizer()
    detector = _detector()
    cam = cv2.VideoCapture(0)

    def generate():
        marked = set()
        while True:
            ok, frame = cam.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
            for (x, y, w, h) in faces:
                face = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                label, confidence = recognizer.predict(face)
                name = 'Unknown'
                if confidence < 75:
                    conn = get_connection()
                    student = conn.execute('SELECT name FROM students WHERE id=?', (label,)).fetchone()
                    conn.close()
                    if student:
                        name = student['name']
                        if label not in marked:
                            mark_attendance(label)
                            marked.add(label)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(frame, f'{name} ({int(confidence)})', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        cam.release()

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/reports')
@login_required()
def reports():
    selected_date = request.args.get('date', date.today().isoformat())
    conn = get_connection()
    rows = conn.execute('''
        SELECT s.roll_no, s.name, s.department, s.year, a.attendance_date, a.attendance_time, a.status
        FROM attendance a JOIN students s ON s.id=a.student_id
        WHERE a.attendance_date=?
        ORDER BY a.attendance_time DESC
    ''', (selected_date,)).fetchall()
    conn.close()
    return render_template('reports.html', rows=rows, selected_date=selected_date)


@app.route('/export')
@login_required()
def export_csv():
    selected_date = request.args.get('date', date.today().isoformat())
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT s.roll_no, s.name, s.department, s.year, a.attendance_date, a.attendance_time, a.status
        FROM attendance a JOIN students s ON s.id=a.student_id
        WHERE a.attendance_date=?
    ''', conn, params=(selected_date,))
    conn.close()
    out = Path('attendance_report.csv')
    df.to_csv(out, index=False)
    return send_file(out, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
