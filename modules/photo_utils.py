import streamlit as st
import os
from PIL import Image, ImageOps

def display_student_photo(name, cohort):
    """
    Finds, crops, and displays the student's photo.
    Splits the image (Left for Y7, Right for Y10), trims the edges,
    and enforces a strict uniform size so all grid photos match perfectly.
    """
    photo_folder = "photos"

    if not os.path.exists(photo_folder):
        st.caption("No photo folder")
        return

    try:
        # Clean up the name to match the file
        safe_name = str(name).strip().lower()
        safe_name = " ".join(safe_name.split())  # Removes double spaces
        safe_name = safe_name.replace(".", "")
        
        filename = f"{safe_name}.png"
        
        # Create a dictionary of lowercase filenames to ensure a match
        files = {f.lower(): f for f in os.listdir(photo_folder)}

        if filename in files:
            img = Image.open(os.path.join(photo_folder, files[filename]))
            w, h = img.size

            # --- THE CROPPING MATH ---
            top_trim = int(h * 0.08)     
            bottom_trim = int(h * 0.13)  # Cuts out the text at the bottom
            
            top = top_trim
            bottom = h - bottom_trim

            # Split left side for Year 7, right side for Year 10
            if cohort == "Year 7":
                crop = (0, top, w // 2, bottom)
            else:
                crop = (w // 2, top, w, bottom)

            img = img.crop(crop)
            
            # --- FORCE UNIFORM SIZE ---
            # ImageOps.fit crops and sizes the image to exactly 140x185 pixels.
            # This ensures perfect grid alignment without stretching faces.
            img = ImageOps.fit(img, (140, 185))

            st.image(img, width=140)
        else:
            st.caption("Photo missing")

    except Exception as e:
        st.caption("Image error")
