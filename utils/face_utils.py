from pathlib import Path
import cv2
import numpy as np

FACE_DIR = Path('dataset/student_faces')


def detect_face(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face = gray[y:y+h, x:x+w]
    return cv2.resize(face, (120, 120))


def save_student_face(roll_no: str, image_file) -> str:
    FACE_DIR.mkdir(parents=True, exist_ok=True)
    path = FACE_DIR / f'{roll_no}.jpg'
    image_file.save(path)
    return str(path)


def compare_faces(captured_face, stored_image_path: str) -> float:
    stored = cv2.imread(stored_image_path)
    if stored is None:
        return 9999
    stored_face = detect_face(stored)
    if stored_face is None:
        return 9999
    return float(np.mean((captured_face.astype('float') - stored_face.astype('float')) ** 2))
