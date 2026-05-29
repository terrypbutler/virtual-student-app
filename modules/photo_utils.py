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
    """
    Display student photo, left half for Year 7, right half for Year 9
    """
    safe_name = str(student_name).strip().replace(".", "")
    filename = f"{safe_name.lower()}.png"

    if filename not in photo_map:
        st.caption("*(Photo not found)*")
        return

    path = os.path.join(PHOTO_FOLDER, photo_map[filename])

    try:
        img = Image.open(path)
        width, height = img.size
        trim_amount = int(height * 0.08)  # trim top/bottom 8%
        top_edge = trim_amount
        bottom_edge = height - trim_amount

        if cohort == "Year 7":
            # Crop left half + trimmed height
            crop_box = (0, top_edge, width // 2, bottom_edge)
        else:  # Year 9
            # Crop right half + trimmed height
            crop_box = (width // 2, top_edge, width, bottom_edge)

        cropped_img = img.crop(crop_box)
        st.image(cropped_img, width=PHOTO_WIDTH)

    except Exception:
        st.caption("*(File is corrupted or not a valid image)*")
