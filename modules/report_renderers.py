import streamlit as st
from PIL import Image
import os

# ---------------------------
# SHARED HELPERS
# ---------------------------
def get_val(row, keys):
    """Safely fetch first available value from multiple possible column names"""
    for k in keys:
        if k in row and str(row[k]).strip():
            return row[k]
    return "N/A"


def render_photo(student_name, cohort):
    """Handles left/right cropped student photos consistently"""

    photo_folder = "photos"

    if not os.path.exists(photo_folder):
        st.caption("*(No photo folder found)*")
        return

    try:
        safe_name = str(student_name).strip().replace(".", "").lower()
        filename = f"{safe_name}.png"

        files = {f.lower(): f for f in os.listdir(photo_folder)}

        if filename not in files:
            st.caption("*(Photo missing)*")
            return

        img = Image.open(os.path.join(photo_folder, files[filename]))
        w, h = img.size

        # crop top/bottom slightly
        trim = int(h * 0.08)
        top = trim
        bottom = h - trim

        if cohort == "Year 7":
            crop = (0, top, w // 2, bottom)   # left side
        else:
            crop = (w // 2, top, w, bottom)   # right side

        img = img.crop(crop)
        st.image(img, width=220)

    except Exception:
        st.caption("*(Image error)*")


# ---------------------------
# BASE PASSPORT LAYOUT
# ---------------------------
def render_passport(row, cohort, title="Student Passport"):
    NAME = "Full Name"
    DOB = "DoB"

    name = str(row.get(NAME, "Unknown Student"))
    dob = str(row.get(DOB, "")).strip()

    header = f"{name} ({dob})" if dob else name

    with st.expander(f"👤 {header}"):

        left, right = st.columns([3, 1])

        with left:
            st.markdown(f"### **{title}: {header}**")

        with right:
            render_photo(name, cohort)

        # ---------------- CORE DATA BLOCK ----------------
        info = {
            "Form Group": ["Form Tutor", "Tutor", "Form Group"],
            "Gender": ["Gender"],
            "SEN Status": ["SEN Status", "SEND Status"],
            "SEN Detail": ["SEN detail", "SEND detail"],
            "Ethnicity": ["Ethnicity"],
            "EAL": ["EAL", "EAL Status"],
            "Disadvantaged": ["Premium", "Disadvantaged", "Pupil Premium"],
            "SATs Reading": ["SATs Reading", "SAT's Reading", "Reading Score"],
            "SATs Maths": ["SATs Maths", "SAT's Maths", "Maths Score"]
        }

        table_html = "<table style='width:100%; border-collapse: collapse;'>"

        for label, keys in info.items():
            table_html += f"""
            <tr>
                <td style='border:1px solid #ddd; padding:8px;'>
                    <strong>{label}:</strong> {get_val(row, keys)}
                </td>
            </tr>
            """

        table_html += "</table>"

        st.markdown(table_html, unsafe_allow_html=True)


# ---------------------------
# YEAR 7 PASSPORTS
# ---------------------------
def render_y7_passports(df):
    st.title("📘 Year 7 Passports")

    if df is None or df.empty:
        st.warning("No students to display.")
        return

    for _, row in df.iterrows():
        render_passport(row, cohort="Year 7", title="Year 7 Passport")


# ---------------------------
# YEAR 9 TRANSITION
# ---------------------------
def render_y9_transition(df):
    st.title("📁 Year 9 Transition Profiles")

    if df is None or df.empty:
        st.warning("No students to display.")
        return

    for _, row in df.iterrows():
        render_passport(row, cohort="Year 9", title="Year 9 Transition Profile")


# ---------------------------
# OPTIONAL EXTENSION (SAFE PLACEHOLDER)
# ---------------------------
def render_subject_report(df):
    """Kept for compatibility (not used in your cleaned app)"""
    st.title("Subject Report")
    st.info("This module is currently disabled in the simplified version.")
