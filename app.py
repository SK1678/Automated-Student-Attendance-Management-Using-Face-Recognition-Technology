from flask import Flask, render_template, request, redirect, url_for, flash
import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Create directories if not exist
if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')
if not os.path.exists('Attendance'):
    os.makedirs('Attendance')

# Path for storing trained model data
TRAINING_DATA_PATH = 'training-data.yml'
FACE_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# Initialize face detector
face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)

# Load recognizer if exists
recognizer = cv2.face.LBPHFaceRecognizer_create()
if os.path.exists(TRAINING_DATA_PATH):
    recognizer.read(TRAINING_DATA_PATH)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Handles image upload and face recognition.
    """
    if 'image' not in request.files:
        flash("No file uploaded!")
        return redirect(url_for('home'))

    file = request.files['image']

    if file.filename == '':
        flash("No file selected!")
        return redirect(url_for('home'))

    if file:
        # Save uploaded image
        img_path = os.path.join('static/uploads', file.filename)
        file.save(img_path)

        # Read and process image
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            flash("No face detected! Try another image.")
            return redirect(url_for('home'))

        # Draw rectangles and recognize faces
        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Try to recognize face
            try:
                label, confidence = recognizer.predict(face_roi)
                name = f"Student_{label}"
                confidence_text = f"{round(100 - confidence, 2)}%"
            except:
                name = "Unknown"
                confidence_text = "N/A"

            # Annotate image
            cv2.putText(img, f"{name} ({confidence_text})", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (36, 255, 12), 2)

        # Save processed image
        processed_path = os.path.join('static/uploads', f"processed_{file.filename}")
        cv2.imwrite(processed_path, img)

        # Record attendance
        record_attendance(name)

        flash("Image processed successfully!")
        return render_template('result.html', image_path=processed_path, name=name)

    return redirect(url_for('home'))


def record_attendance(name):
    """
    Logs attendance into a CSV file.
    """
    date_today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"Attendance/Attendance_{date_today}.csv"

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=['Name', 'Date', 'Time'])

    if name not in df['Name'].values:
        now = datetime.now()
        time_string = now.strftime("%H:%M:%S")
        df.loc[len(df)] = [name, date_today, time_string]
        df.to_csv(file_path, index=False)


@app.route('/train', methods=['POST'])
def train_model():
    """
    Train the face recognition model with uploaded student images.
    """
    dataset_path = 'dataset'
    if not os.path.exists(dataset_path):
        flash("No dataset found. Please add student images to 'dataset/' folder.")
        return redirect(url_for('home'))

    faces, ids = [], []
    for student_id, student_folder in enumerate(os.listdir(dataset_path)):
        folder_path = os.path.join(dataset_path, student_folder)
        for img_name in os.listdir(folder_path):
            img_path = os.path.join(folder_path, img_name)
            img = Image.open(img_path).convert('L')  # grayscale
            img_np = np.array(img, 'uint8')
            faces.append(img_np)
            ids.append(student_id)

    recognizer.train(faces, np.array(ids))
    recognizer.save(TRAINING_DATA_PATH)
    flash("Model trained successfully!")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
