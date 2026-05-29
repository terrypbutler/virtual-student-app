import os
import streamlit as st
import numpy as np
import cv2
from PIL import Image

from config import PHOTO_FOLDER, PHOTO_WIDTH


@st.cache_resource
def get_photo_map():
    if not os.path.exists(PHOTO_FOLDER):
        return {}

    files = os.listdir(PHOTO_FOLDER)
    return {f.lower(): f for f in files}


photo_map = get_photo_map()


# ---------------------------
# FACE DETECTION SETUP
# ---------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


def detect_face_center(cv_img):
    """
    Returns (x, y, w, h) of first detected face or None
    """
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(50, 50)
    )

    if len(faces) == 0:
        return None

    # take largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return faces[0]


def smart_crop(img):
    """
    Face-centred crop with fallback to center crop
    """

    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    h, w = cv_img.shape[:2]

    face = detect_face_center(cv_img)

    crop_width = w // 2
    crop_height = int(h * 0.85)

    if face is not None:
        x, y, fw, fh = face
        center_x = x + fw // 2
        center_y = y + fh // 2
    else:
        # fallback: image centre
        center_x = w // 2
        center_y = h // 2

    x1 = max(0, center_x - crop_width // 2)
    x2 = min(w, center_x + crop_width // 2)

    y1 = max(0, center_y - crop_height // 2)
    y2 = min(h, center_y + crop_height // 2)

    cropped = img.crop((x1, y1, x2, y2))

    return cropped


def display_student_photo(student_name, cohort="Year 7"):
    safe_name = str(student_name).strip().replace(".", "")
    filename = f"{safe_name.lower()}.png"

    if filename not in photo_map:
        st.caption("Photo not found")
        return

    path = os.path.join(PHOTO_FOLDER, photo_map[filename])

    try:
        img = Image.open(path)

        cropped = smart_crop(img)

        st.image(cropped, width=PHOTO_WIDTH)

    except Exception:
        st.caption("Corrupted image")
        #
