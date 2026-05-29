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
        img = load_student_image(row.get("Full Name", ""), selected_cohort)

if img:
    st.image(img, width=140)
else:
    st.caption("📷 No photo found")

    except Exception:
        st.caption("*(Image error)*")


# ---------------------------
# BASE PASSPORT LAYOUT
# ---------------------------
def render_student_passport(student_row, cohort):
    """
    Render a MIS-style student passport with photo and details.
    """
    import os
    from PIL import Image
    import streamlit as st

    NAME_COLUMN = "Full Name"
    DOB_COLUMN = "DoB"

    # Get student name and DoB
    s_name = str(student_row.get(NAME_COLUMN, "Unknown Student"))
    s_dob = str(student_row.get(DOB_COLUMN, "")).strip()
    header = f"{s_name} ({s_dob})" if s_dob else s_name

    with st.expander(f"👤 {header}"):
        left, right = st.columns([1, 2])

        # ---------------- LEFT COLUMN: PHOTO ----------------
        def load_student_image(name, cohort):
            """Safely load and crop student image."""
            try:
                safe_name = name.strip().replace(".", "").lower()
                filename = f"{safe_name}.png"
                photo_folder = "photos"
                if not os.path.exists(photo_folder):
                    return None

                files = {f.lower(): f for f in os.listdir(photo_folder)}
                if filename not in files:
                    return None

                img = Image.open(os.path.join(photo_folder, files[filename]))
                w, h = img.size
                trim = int(h * 0.08)
                top = trim
                bottom = h - trim

                if cohort == "Year 7":
                    crop = (0, top, w // 2, bottom)      # left half
                else:
                    crop = (w // 2, top, w, bottom)      # right half

                return img.crop(crop)
            except:
                return None

        img = load_student_image(s_name, cohort)
        if img:
            left.image(img, width=140, caption=s_name)
        else:
            left.info("📷 No photo found")

        # ---------------- RIGHT COLUMN: DETAILS ----------------
        def get_val(keys):
            for k in keys:
                if k in student_row and str(student_row[k]).strip():
                    return student_row[k]
            return "N/A"

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

        # ----------------- Styled card -----------------
        card_style = """
        <style>
        .passport-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            background-color: #f9f9f9;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }
        .passport-card td {
            padding: 6px 8px;
        }
        </style>
        """
        st.markdown(card_style, unsafe_allow_html=True)

        table_html = "<div class='passport-card'><table style='width:100%; border-collapse: collapse;'>"
        for label, keys in info.items():
            table_html += f"""
            <tr>
                <td style='border-bottom:1px solid #eee;'>
                    <strong>{label}:</strong> {get_val(keys)}
                </td>
            </tr>
            """
        table_html += "</table></div>"

        right.markdown(table_html, unsafe_allow_html=True)

# ---------------------------
# YEAR 7 PASSPORTS
# ---------------------------
def render_y7_passports(df):
    st.title("📘 Year 7 Passports")

    for _, row in df.iterrows():
        st.subheader(row.get("Full Name", "Unknown"))

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write("Form Group:", row.get("Form Group", "N/A"))
            st.write("Gender:", row.get("Gender", "N/A"))
            st.write("SEN:", row.get("SEN Status", "N/A"))
            st.write("Ethnicity:", row.get("Ethnicity", "N/A"))

        with col2:
            st.image("photos/" + row.get("Full Name","").lower().replace(".","") + ".png",
                     width=140, clamp=True)


# ---------------------------
# YEAR 9 TRANSITION
# ---------------------------
def render_y9_transition(df):
    st.title("📁 Year 9 Transition")

    for _, row in df.iterrows():
        st.subheader(row.get("Full Name", "Unknown"))

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write("Form Group:", row.get("Form Group", "N/A"))
            st.write("Gender:", row.get("Gender", "N/A"))
            st.write("SEN:", row.get("SEN Status", "N/A"))

        with col2:
            st.image("photos/" + row.get("Full Name","").lower().replace(".","") + ".png",
                     width=140, clamp=True)


# ---------------------------
# OPTIONAL EXTENSION (SAFE PLACEHOLDER)
# ---------------------------
def render_subject_report(df):
    """Kept for compatibility (not used in your cleaned app)"""
    st.title("Subject Report")
    st.info("This module is currently disabled in the simplified version.")
