from datetime import datetime, date
from pathlib import Path
import csv
import cv2
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from utils.database import get_db_connection, init_db
from utils.face_utils import save_student_face, detect_face, compare_faces
from utils.email_alert import send_email_notification

app = Flask(__name__)
app.secret_key = 'change-this-secret-key'
init_db()


def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
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
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    total_students = conn.execute('SELECT COUNT(*) AS c FROM students').fetchone()['c']
    today_count = conn.execute('SELECT COUNT(*) AS c FROM attendance WHERE attendance_date=?', (str(date.today()),)).fetchone()['c']
    total_attendance = conn.execute('SELECT COUNT(*) AS c FROM attendance').fetchone()['c']
    recent = conn.execute('''SELECT s.roll_no, s.name, a.attendance_date, a.attendance_time, a.status
                             FROM attendance a JOIN students s ON a.student_id=s.id
                             ORDER BY a.id DESC LIMIT 8''').fetchall()
    conn.close()
    return render_template('dashboard.html', total_students=total_students, today_count=today_count,
                           total_attendance=total_attendance, recent=recent)


@app.route('/register-student', methods=['GET', 'POST'])
@login_required
def register_student():
    if request.method == 'POST':
        roll_no = request.form['roll_no'].strip()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        department = request.form['department'].strip()
        image = request.files.get('face_image')
        face_path = save_student_face(roll_no, image) if image and image.filename else ''
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO students (roll_no,name,email,department,face_image) VALUES (?,?,?,?,?)',
                         (roll_no, name, email, department, face_path))
            conn.commit()
            flash('Student registered successfully.', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('students'))
    return render_template('register_student.html')


@app.route('/students')
@login_required
def students():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('students.html', students=rows)


@app.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if request.method == 'POST':
        image = request.files.get('capture_image')
        if not image:
            flash('Please upload a face image.', 'warning')
            return redirect(url_for('mark_attendance'))
        temp_path = Path('instance/temp_capture.jpg')
        temp_path.parent.mkdir(exist_ok=True)
        image.save(temp_path)
        captured = cv2.imread(str(temp_path))
        captured_face = detect_face(captured)
        if captured_face is None:
            flash('No face detected. Try another image.', 'danger')
            return redirect(url_for('mark_attendance'))

        conn = get_db_connection()
        students = conn.execute('SELECT * FROM students WHERE face_image IS NOT NULL AND face_image != ""').fetchall()
        best_student, best_score = None, 9999
        for student in students:
            score = compare_faces(captured_face, student['face_image'])
            if score < best_score:
                best_student, best_score = student, score

        if best_student and best_score < 2500:
            now = datetime.now()
            try:
                conn.execute('INSERT INTO attendance (student_id,attendance_date,attendance_time,status) VALUES (?,?,?,?)',
                             (best_student['id'], str(date.today()), now.strftime('%H:%M:%S'), 'Present'))
                conn.commit()
                send_email_notification(best_student['email'], 'Attendance Marked',
                                        f"Hi {best_student['name']}, your attendance was marked on {date.today()} at {now.strftime('%H:%M:%S')}.")
                flash(f"Attendance marked for {best_student['name']} ({best_student['roll_no']}).", 'success')
            except Exception:
                flash('Attendance already marked today for this student.', 'info')
        else:
            flash('Face not matched with registered students.', 'danger')
        conn.close()
        return redirect(url_for('reports'))
    return render_template('mark_attendance.html')


@app.route('/reports')
@login_required
def reports():
    filter_date = request.args.get('date', '')
    conn = get_db_connection()
    if filter_date:
        rows = conn.execute('''SELECT s.roll_no, s.name, s.department, a.attendance_date, a.attendance_time, a.status
                               FROM attendance a JOIN students s ON a.student_id=s.id
                               WHERE a.attendance_date=? ORDER BY a.attendance_time DESC''', (filter_date,)).fetchall()
    else:
        rows = conn.execute('''SELECT s.roll_no, s.name, s.department, a.attendance_date, a.attendance_time, a.status
                               FROM attendance a JOIN students s ON a.student_id=s.id
                               ORDER BY a.id DESC''').fetchall()
    conn.close()
    return render_template('reports.html', records=rows, filter_date=filter_date)


@app.route('/export')
@login_required
def export_csv():
    export_path = Path('exports/attendance_report.csv')
    export_path.parent.mkdir(exist_ok=True)
    conn = get_db_connection()
    rows = conn.execute('''SELECT s.roll_no, s.name, s.department, a.attendance_date, a.attendance_time, a.status
                           FROM attendance a JOIN students s ON a.student_id=s.id ORDER BY a.id DESC''').fetchall()
    conn.close()
    with open(export_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Roll No', 'Name', 'Department', 'Date', 'Time', 'Status'])
        for r in rows:
            writer.writerow(list(r))
    return send_file(export_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
