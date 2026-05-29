import streamlit as st
import pandas as pd
from PIL import Image
import os

from modules.data_loader import load_data
from modules.report_renderers import (
    render_y7_passports,
    render_subject_report,
    render_y9_transition,
    render_y9_full
)

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Virtual Student MIS", layout="wide")

YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"


# ---------------------------
# DATA LOAD
# ---------------------------
selected_cohort = st.sidebar.radio("📅 Cohort", ["Year 7", "Year 9"])
df = load_data(YEAR_7_URL if selected_cohort == "Year 7" else YEAR_9_URL)


# ---------------------------
# SIDEBAR NAV
# ---------------------------
st.sidebar.title("🎓 School MIS Dashboard")

page = st.sidebar.radio(
    "Navigate",
    [
        "Student Search",
        "Year 7 Passports",
        "Year 7 Reports",
        "Year 9 Transition",
        "Year 9 Full Reports",
        "Analytics"
    ]
)


# ---------------------------
# STUDENT PASSPORT RENDERER (USED BY SEARCH)
# ---------------------------
def render_student_passport(student_row, cohort):
    NAME_COLUMN = "Full Name"
    DOB_COLUMN = "DoB"

    s_name = str(student_row.get(NAME_COLUMN, "Unknown Student"))
    s_dob = str(student_row.get(DOB_COLUMN, "")).strip()
    header = f"{s_name} ({s_dob})" if s_dob else s_name

    with st.expander(f"👤 {header}"):

        left, right = st.columns([3, 1])

        with left:
            st.markdown(f"### **{header}**")

        # ---------------- PHOTO ----------------
        photo_folder = "photos"

        if os.path.exists(photo_folder):
            try:
                safe_name = s_name.strip().replace(".", "").lower()
                filename = f"{safe_name}.png"

                files = {f.lower(): f for f in os.listdir(photo_folder)}

                if filename in files:
                    img = Image.open(os.path.join(photo_folder, files[filename]))
                    w, h = img.size

                    trim = int(h * 0.08)
                    top = trim
                    bottom = h - trim

                    if cohort == "Year 7":
                        crop = (0, top, w // 2, bottom)
                    else:
                        crop = (w // 2, top, w, bottom)

                    img = img.crop(crop)
                    right.image(img, width=220)

                else:
                    right.caption("*(Photo missing)*")

            except:
                right.caption("*(Image error)*")
        else:
            right.caption("*(No photo folder)*")

        # ---------------- DETAILS ----------------
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

st.markdown("### 📋 Student Summary")

for label, keys in info.items():
    value = get_val(keys)

    col1, col2 = st.columns([1, 2])
    col1.markdown(f"**{label}**")
    col2.markdown(str(value))


# ---------------------------
# SEARCH PAGE (NOW MATCHES REPORT STYLE)
# ---------------------------
def student_search(df):
    st.title("🔍 Student Search (MIS View)")

    query = st.text_input("Search student name")

    if query:
        results = df[df["Full Name"].str.contains(query, case=False, na=False)]

        st.write(f"Found {len(results)} students")

        if len(results) == 0:
            st.warning("No matches found.")

        for _, row in results.iterrows():
            render_student_passport(row, selected_cohort)


# ---------------------------
# ANALYTICS (NO MATPLOTLIB)
# ---------------------------
def analytics(df):
    st.title("📊 Cohort Analytics Dashboard")

    st.subheader("Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Students", len(df))

    if "SEN Status" in df.columns:
        col2.metric("SEN", (df["SEN Status"].fillna("") != "").sum())

    if "EAL" in df.columns:
        col3.metric("EAL", (df["EAL"].fillna("") != "").sum())

    st.write("---")

    if "SEN Status" in df.columns:
        st.subheader("SEN Distribution")
        st.bar_chart(df["SEN Status"].value_counts())

    if "EAL" in df.columns:
        st.subheader("EAL Distribution")
        st.bar_chart(df["EAL"].value_counts())

    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True)


# ---------------------------
# ROUTING
# ---------------------------
if page == "Student Search":
    student_search(df)

elif page == "Year 7 Passports":
    render_y7_passports(df)

elif page == "Year 7 Reports":
    render_subject_report(df)

elif page == "Year 9 Transition":
    render_y9_transition(df)

elif page == "Year 9 Full Reports":
    render_y9_full(df)

elif page == "Analytics":
    analytics(df)
