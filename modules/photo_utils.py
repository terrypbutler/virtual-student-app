import os
import streamlit as st
from PIL import Image

from config import PHOTO_FOLDER, PHOTO_WIDTH

@st.cache_resource
def get_photo_map():
    if not os.path.exists(PHOTO_FOLDER):
        return {}

    files = os.listdir(PHOTO_FOLDER)
    return {f.lower(): f for f in files}

photo_map = get_photo_map()


def display_student_photo(student_name, cohort="Year 7"):
    safe_name = str(student_name).strip().replace(".", "")
    filename = f"{safe_name.lower()}.png"

    if filename not in photo_map:
        st.caption("Photo not found")
        return

    path = os.path.join(PHOTO_FOLDER, photo_map[filename])

    try:
        img = Image.open(path)

        width, height = img.size
        crop_margin = int(height * 0.08)

        # 👇 KEY CHANGE: LEFT vs RIGHT split logic
        if cohort == "Year 7":
            crop_box = (
                0,
                crop_margin,
                width // 2,
                height - crop_margin
            )
        else:  # Year 9
            crop_box = (
                width // 2,
                crop_margin,
                width,
                height - crop_margin
            )

        cropped = img.crop(crop_box)

        st.image(cropped, width=PHOTO_WIDTH)

    except Exception:
        st.caption("Corrupted image")
