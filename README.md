# Face Recognition Attendance System

A comprehensive web-based face recognition attendance system with separate admin and student portals. The system uses grayscale image processing for optimal performance and includes advanced features like semester migration, ID blocking, and attendance report generation.

## 🎯 Features

### Admin Portal
- **Student Enrollment**: Register new students with face capture and personal details
- **Student Management**: View all enrolled students with search functionality
- **Semester Migration**: Easily migrate students to new semesters
- **ID Blocking/Unblocking**: Control student access to the system
- **Attendance Reports**: 
  - Daily attendance reports
  - Semester-wise attendance reports
  - Download as Excel files

### Student Portal
- **ID-based Login**: Secure access using student ID
- **Personal Dashboard**: View attendance statistics and records
- **Attendance History**: See all past attendance records
- **Monthly Statistics**: Track attendance trends

### Attendance System
- **Real-time Face Recognition**: Fast and accurate recognition using grayscale processing
- **Live Camera Feed**: Capture attendance through webcam
- **Duplicate Prevention**: Can't mark attendance twice on same day
- **Instant Verification**: Immediate feedback on recognition

## 🚀 Technology Stack

- **Backend**: Flask (Python)
- **Face Recognition**: face_recognition library with dlib
- **Image Processing**: OpenCV (grayscale conversion for efficiency)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **UI Components**: Font Awesome, SweetAlert2
- **Data Storage**: Pickle files (easily replaceable with database)
- **Reports**: Pandas, openpyxl for Excel generation

## 📋 Prerequisites

- Python 3.8 or higher
- Webcam for face capture
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation

### 1. Install System Dependencies (for face_recognition)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake
sudo apt-get install -y libopenblas-dev liblapack-dev
sudo apt-get install -y libx11-dev libgtk-3-dev
```

**macOS:**
```bash
brew install cmake
brew install dlib
```

**Windows:**
- Install Visual Studio Build Tools
- Download and install CMake from https://cmake.org/download/

### 2. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd face-recognition-attendance

# Or simply download and extract the ZIP file
```

### 3. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: If face_recognition installation fails, try:
```bash
pip install dlib --break-system-packages
pip install face-recognition --break-system-packages
```

### 5. Verify Installation

```bash
python -c "import face_recognition; print('Face recognition installed successfully!')"
```

## 🎮 Running the Application

### 1. Start the Server

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 2. Access the Portals

Open your web browser and navigate to:
- **Home Page**: http://localhost:5000
- **Admin Portal**: http://localhost:5000/admin/login
  - Username: `admin`
  - Password: `admin123`
- **Student Portal**: http://localhost:5000/student/login
  - Use enrolled student ID
- **Mark Attendance**: http://localhost:5000/attendance

## 📖 Usage Guide

### For Administrators

1. **Login to Admin Portal**
   - Use credentials: admin/admin123

2. **Enroll New Student**
   - Click "Enroll Student" from dashboard
   - Fill in student details (ID, Name, Semester, Department)
   - Capture student's face using webcam
   - System will process grayscale image and store face encoding
   - Click "Enroll Student"

3. **Manage Students**
   - View all students in the Students page
   - Search for specific students
   - Migrate students to new semester
   - Block/unblock student IDs

4. **Download Reports**
   - Daily Report: Downloads today's attendance
   - Semester Report: Select semester and department, then download

### For Students

1. **Login to Student Portal**
   - Enter your Student ID
   - Access your personal dashboard

2. **View Attendance**
   - See today's status (Present/Absent)
   - View monthly attendance count
   - Check total attendance days
   - View recent attendance history

3. **Mark Attendance**
   - Go to "Mark Attendance" page
   - Allow camera access
   - Position face in camera view
   - Click "Capture & Mark Attendance"
   - Wait for recognition
   - Receive confirmation

## 🎨 UI Features

- **Modern Gradient Design**: Eye-catching gradients and animations
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Interactive Cards**: Hover effects and smooth transitions
- **Real-time Feedback**: SweetAlert2 notifications for all actions
- **Icon Integration**: Font Awesome icons throughout
- **Professional Tables**: Sortable and searchable data tables

## 🔧 Configuration

### Change Admin Credentials

Edit `app.py` around line 82:
```python
if data.get('username') == 'your_username' and data.get('password') == 'your_password':
```

### Change Secret Key

Edit `app.py` around line 16:
```python
app.secret_key = 'your-secure-secret-key-here'
```

### Adjust Face Recognition Tolerance

Edit `app.py` around line 288:
```python
matches = face_recognition.compare_faces([stored_encoding], face_encodings[0], tolerance=0.6)
```
- Lower value (0.4-0.5): More strict, fewer false positives
- Higher value (0.6-0.7): More lenient, fewer false negatives

## 📁 Project Structure

```
face-recognition-attendance/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── data/                       # Data storage (auto-created)
│   ├── students.pkl           # Student information
│   ├── encodings.pkl          # Face encodings
│   └── attendance.pkl         # Attendance records
│
├── static/                     # Static files
│   ├── css/
│   │   └── style.css          # Custom styles
│   └── student_images/        # Student photos (auto-created)
│
└── templates/                  # HTML templates
    ├── base.html              # Base template
    ├── index.html             # Landing page
    ├── admin_login.html       # Admin login
    ├── admin_dashboard.html   # Admin dashboard
    ├── admin_enroll.html      # Student enrollment
    ├── admin_students.html    # Student management
    ├── student_login.html     # Student login
    ├── student_dashboard.html # Student dashboard
    └── attendance.html        # Attendance marking
```

## 🔒 Security Notes

- Change default admin credentials before deployment
- Use environment variables for sensitive data
- Implement HTTPS in production
- Add CSRF protection for forms
- Consider adding rate limiting
- Implement proper session management

## 🚀 Production Deployment

For production deployment:

1. **Use a Production WSGI Server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Use a Proper Database**: Replace pickle files with PostgreSQL/MySQL

3. **Add Environment Variables**:
   ```python
   import os
   app.secret_key = os.environ.get('SECRET_KEY')
   ```

4. **Enable HTTPS**: Use nginx as reverse proxy with SSL certificate

5. **Set up Logging**: Implement proper logging for monitoring

## 🐛 Troubleshooting

### Camera Not Working
- Check browser permissions for camera access
- Ensure camera is not being used by another application
- Try a different browser

### Face Not Recognized
- Ensure good lighting conditions
- Face the camera directly
- Remove glasses or face coverings
- Re-enroll the student if issues persist

### Installation Errors
- Make sure you have all system dependencies installed
- Try installing dlib separately first
- Check Python version compatibility (3.8+)

### Slow Performance
- Reduce image resolution in code
- Adjust face recognition tolerance
- Use a faster computer/server

## 📝 Future Enhancements

- [ ] Database integration (PostgreSQL/MySQL)
- [ ] Email notifications for attendance reports
- [ ] Mobile app integration
- [ ] Attendance calendar view
- [ ] Bulk student enrollment via CSV
- [ ] Multi-camera support
- [ ] Attendance analytics and charts
- [ ] Leave management system
- [ ] Parent portal access

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Test in a clean environment

## 🙏 Acknowledgments

- face_recognition library by Adam Geitgey
- Flask framework
- Bootstrap for UI components
- OpenCV for image processing
- Font Awesome for icons

---

**Note**: This is a basic implementation for educational purposes. For production use, implement proper security measures, database integration, and scalability considerations.