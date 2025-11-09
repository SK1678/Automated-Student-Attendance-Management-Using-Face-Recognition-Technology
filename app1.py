from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import cv2
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
import pandas as pd
from functools import wraps
import io
import base64

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Session Configuration - AUTO EXPIRATION AFTER 2 HOURS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Auto-refresh session on activity

# Create necessary directories
os.makedirs('data', exist_ok=True)
os.makedirs('static/student_images', exist_ok=True)

# File paths
STUDENTS_FILE = 'data/students.pkl'
FACES_FILE = 'data/faces.pkl'
ATTENDANCE_FILE = 'data/attendance.pkl'

# Initialize face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize data files
def initialize_data():
    if not os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'wb') as f:
            pickle.dump({}, f)
    if not os.path.exists(FACES_FILE):
        with open(FACES_FILE, 'wb') as f:
            pickle.dump({}, f)
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'wb') as f:
            pickle.dump([], f)

initialize_data()

# Session management
@app.before_request
def make_session_permanent():
    """Make sessions permanent and track activity"""
    session.permanent = True
    if 'admin' in session or 'student_id' in session:
        session['last_activity'] = datetime.now().isoformat()

def check_session_timeout():
    """Check if session has expired (2 hours of inactivity)"""
    if 'login_time' in session:
        login_time = datetime.fromisoformat(session['login_time'])
        now = datetime.now()
        # Check if session is older than 2 hours
        if now - login_time > timedelta(hours=2):
            return True
    return False

# Helper functions
def load_students():
    try:
        with open(STUDENTS_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

def save_students(students):
    with open(STUDENTS_FILE, 'wb') as f:
        pickle.dump(students, f)

def load_faces():
    try:
        with open(FACES_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

def save_faces(faces):
    with open(FACES_FILE, 'wb') as f:
        pickle.dump(faces, f)

def load_attendance():
    try:
        with open(ATTENDANCE_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return []

def save_attendance(attendance):
    with open(ATTENDANCE_FILE, 'wb') as f:
        pickle.dump(attendance, f)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        # Check for session timeout
        if check_session_timeout():
            session.clear()
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('student_login'))
        # Check for session timeout
        if check_session_timeout():
            session.clear()
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

def extract_face_features(image):
    """Extract simple face features using OpenCV"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        return None, "No face detected"
    
    if len(faces) > 1:
        return None, "Multiple faces detected"
    
    (x, y, w, h) = faces[0]
    face_roi = gray[y:y+h, x:x+w]
    face_roi = cv2.resize(face_roi, (100, 100))
    
    return face_roi.flatten(), None

def compare_faces(face1, face2, threshold=3000):
    """Compare two face features using simple correlation"""
    if face1 is None or face2 is None:
        return False
    
    # Calculate mean squared error
    mse = np.mean((face1 - face2) ** 2)
    return mse < threshold

# 🥚 EASTER EGG: Secret coffee break endpoint
@app.route('/coffee')
def coffee_break():
    """Easter egg route - returns HTTP 418 I'm a teapot"""
    return jsonify({
        'error': 'I\'m a teapot',
        'message': '☕ This attendance system runs on coffee, not tea!',
        'tip': 'The developer was probably on their 5th cup when they wrote this.',
        'status': 418
    }), 418

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    """Keep session alive - used for session refresh"""
    return jsonify({'status': 'ok', 'message': 'Session refreshed'})

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.json
        # Simple authentication (CHANGE IN PRODUCTION!)
        if data.get('username') == 'admin' and data.get('password') == 'admin123':
            session['admin'] = True
            session['login_time'] = datetime.now().isoformat()
            session['user_type'] = 'admin'
            session.permanent = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    students = load_students()
    active_students = sum(1 for s in students.values() if not s.get('blocked', False))
    
    # Get today's attendance count (unique students)
    attendance_records = load_attendance()
    today = datetime.now().strftime('%Y-%m-%d')
    today_students = set(r['student_id'] for r in attendance_records if r['date'] == today)
    today_count = len(today_students)
    
    return render_template('admin_dashboard.html', 
                         total_students=len(students),
                         active_students=active_students,
                         today_attendance=today_count)

@app.route('/admin/enroll', methods=['GET', 'POST'])
@admin_required
def admin_enroll():
    if request.method == 'POST':
        data = request.json
        student_id = data.get('student_id')
        name = data.get('name')
        semester = data.get('semester')
        department = data.get('department')
        image_data = data.get('image')
        
        try:
            # Decode base64 image
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Extract face features
            face_features, error = extract_face_features(image)
            
            if error:
                return jsonify({'success': False, 'message': error})
            
            # Save student data
            students = load_students()
            
            if student_id in students:
                return jsonify({'success': False, 'message': 'Student ID already exists'})
            
            students[student_id] = {
                'name': name,
                'semester': semester,
                'department': department,
                'enrolled_date': datetime.now().strftime('%Y-%m-%d'),
                'enrolled_by': 'admin',
                'blocked': False
            }
            save_students(students)
            
            # Save face features
            faces = load_faces()
            faces[student_id] = face_features
            save_faces(faces)
            
            # Save student image
            os.makedirs('static/student_images', exist_ok=True)
            cv2.imwrite(f'static/student_images/{student_id}.jpg', image)
            
            return jsonify({'success': True, 'message': 'Student enrolled successfully'})
        
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
    return render_template('admin_enroll.html')

@app.route('/admin/students')
@admin_required
def admin_students():
    students = load_students()
    return render_template('admin_students.html', students=students)

@app.route('/admin/migrate_semester', methods=['POST'])
@admin_required
def migrate_semester():
    data = request.json
    student_id = data.get('student_id')
    new_semester = data.get('new_semester')
    
    students = load_students()
    if student_id in students:
        students[student_id]['semester'] = new_semester
        students[student_id]['last_modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_students(students)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Student not found'})

@app.route('/admin/block_student', methods=['POST'])
@admin_required
def block_student():
    data = request.json
    student_id = data.get('student_id')
    
    students = load_students()
    if student_id in students:
        students[student_id]['blocked'] = not students[student_id].get('blocked', False)
        students[student_id]['last_modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_students(students)
        return jsonify({'success': True, 'blocked': students[student_id]['blocked']})
    return jsonify({'success': False, 'message': 'Student not found'})

@app.route('/admin/download_attendance')
@admin_required
def download_attendance():
    report_type = request.args.get('type', 'daily')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    attendance_records = load_attendance()
    students = load_students()
    
    if report_type == 'daily':
        filtered = [r for r in attendance_records if r['date'] == date_str]
        filename = f'attendance_{date_str}.xlsx'
    else:  # semester
        semester = request.args.get('semester')
        department = request.args.get('department')
        filtered = [r for r in attendance_records 
                   if students.get(r['student_id'], {}).get('semester') == semester
                   and students.get(r['student_id'], {}).get('department') == department]
        filename = f'attendance_{semester}_{department}.xlsx'
    
    # Create DataFrame
    data = []
    for record in filtered:
        student = students.get(record['student_id'], {})
        data.append({
            'Student ID': record['student_id'],
            'Name': student.get('name', 'Unknown'),
            'Department': student.get('department', 'Unknown'),
            'Semester': student.get('semester', 'Unknown'),
            'Date': record['date'],
            'Time': record['time']
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
    output.seek(0)
    
    return send_file(output, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=filename)

# Student Routes
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        data = request.json
        student_id = data.get('student_id')
        
        students = load_students()
        if student_id in students:
            if students[student_id].get('blocked', False):
                return jsonify({'success': False, 'message': 'Your account has been blocked. Please contact administrator.'})
            session['student_id'] = student_id
            session['login_time'] = datetime.now().isoformat()
            session['user_type'] = 'student'
            session.permanent = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid Student ID'})
    
    return render_template('student_login.html')

@app.route('/student/logout')
def student_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session['student_id']
    students = load_students()
    student = students.get(student_id, {})
    
    attendance_records = load_attendance()
    student_attendance = [r for r in attendance_records if r['student_id'] == student_id]
    
    # Calculate statistics
    today = datetime.now().strftime('%Y-%m-%d')
    this_month = datetime.now().strftime('%Y-%m')
    
    today_present = any(r['date'] == today for r in student_attendance)
    month_count = sum(1 for r in student_attendance if r['date'].startswith(this_month))
    total_count = len(student_attendance)
    
    # Calculate attendance percentage (assuming 20 working days per month)
    month_percentage = (month_count / 20 * 100) if month_count > 0 else 0
    
    return render_template('student_dashboard.html',
                         student=student,
                         student_id=student_id,
                         today_present=today_present,
                         month_attendance=month_count,
                         total_attendance=total_count,
                         month_percentage=round(month_percentage, 1),
                         attendance_records=student_attendance[-10:])

# Face Recognition Attendance
@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    image_data = data.get('image')
    
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Extract face features
        face_features, error = extract_face_features(image)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        # Compare with stored faces
        faces = load_faces()
        students = load_students()
        
        best_match = None
        best_score = float('inf')
        
        for student_id, stored_features in faces.items():
            if compare_faces(face_features, stored_features):
                mse = np.mean((face_features - stored_features) ** 2)
                if mse < best_score:
                    best_score = mse
                    best_match = student_id
        
        if best_match:
            # Check if student is blocked
            if students[best_match].get('blocked', False):
                return jsonify({'success': False, 'message': 'Your account has been blocked. Please contact administrator.'})
            
            # ✅ FIXED: Now allows multiple attendance entries per day
            attendance_records = load_attendance()
            
            # Mark attendance with current timestamp
            attendance_records.append({
                'student_id': best_match,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'method': 'face_recognition'
            })
            save_attendance(attendance_records)
            
            return jsonify({'success': True, 
                          'message': f'Attendance marked successfully for {students[best_match]["name"]}',
                          'student_id': best_match,
                          'name': students[best_match]['name'],
                          'department': students[best_match]['department'],
                          'semester': students[best_match]['semester']})
        
        return jsonify({'success': False, 'message': 'Face not recognized. Please try again or contact administrator.'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/check_session')
def check_session():
    """API endpoint to check session status"""
    if 'admin' in session or 'student_id' in session:
        if check_session_timeout():
            return jsonify({'valid': False, 'message': 'Session expired'})
        
        login_time = datetime.fromisoformat(session['login_time'])
        remaining = timedelta(hours=2) - (datetime.now() - login_time)
        remaining_minutes = int(remaining.total_seconds() / 60)
        
        return jsonify({
            'valid': True, 
            'user_type': session.get('user_type'),
            'remaining_minutes': remaining_minutes
        })
    return jsonify({'valid': False, 'message': 'No active session'})

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 Face Recognition Attendance System")
    print("=" * 60)
    print("✅ Server starting...")
    print("📱 Access the application at:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000")
    print("\n🔑 Default Admin Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n⏰ Session Expiration: 2 hours")
    print("\n☕ Secret: Try visiting /coffee for a surprise!")
    print("\n⚠️  Press CTRL+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)