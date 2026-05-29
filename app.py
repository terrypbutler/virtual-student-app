import streamlit as st
import pandas as pd
from PIL import Image
import os

def safe_unique(df, col):
    if col in df.columns:
        return sorted(df[col].dropna().astype(str).unique().tolist())
    return []

from modules.data_loader import load_data
from modules.report_renderers import render_y7_passports, render_y9_transition
# --------------------------- SAFE IMAGE LOADER ---------------------------
import os
from PIL import Image

def load_student_image(name, cohort):
    folder = "photos"

    if not os.path.exists(folder):
        return None

    safe_name = str(name).strip().lower()
    safe_name = " ".join(safe_name.split())  # removes double spaces
    safe_name = safe_name.replace(".", "")

    expected_file = f"{safe_name}.png"

    files = {f.lower(): f for f in os.listdir(folder)}

    if expected_file not in files:
        return None

    path = os.path.join(folder, files[expected_file])

    try:
        return Image.open(path)
    except:
        return None
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
        "Year 9 Transition",
        "Analytics"
    ],
    key="sidebar_nav"
)

# ---------------------------
# STUDENT PASSPORT RENDERER
# ---------------------------
def render_student_passport(student_row, cohort):
    import streamlit as st
    import os
    from PIL import Image

    NAME_COLUMN = "Full Name"
    DOB_COLUMN = "DoB"

    s_name = str(student_row.get(NAME_COLUMN, "Unknown Student"))
    s_dob = str(student_row.get(DOB_COLUMN, "")).strip()
    header = f"{s_name} ({s_dob})" if s_dob else s_name

    with st.expander(f"👤 {header}"):

        left, right = st.columns([3, 1])

        # ---------------- LEFT (DETAILS) ----------------
        with left:

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

            cols = st.columns(2)

            items = list(info.items())
            for i, (label, keys) in enumerate(items):
                value = get_val(keys)
                cols[i % 2].metric(label, value)

        # ---------------- RIGHT (PHOTO) ----------------
        with right:
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
                        st.image(img, width=140)
                    else:
                        st.caption("Photo missing")

                except:
                    st.caption("Image error")
            else:
                st.caption("No photo folder")
# ---------------------------
# SEARCH PAGE
# ---------------------------
def student_search(df):
    st.title("🔍 Student Search (MIS View)")
    query = st.text_input("Search student name", key="search_name")

    if query:
        results = df[df["Full Name"].str.contains(query, case=False, na=False)]
        st.write(f"Found {len(results)} students")

        if len(results) == 0:
            st.warning("No matches found.")

        for _, row in results.iterrows():
            render_student_passport(row, selected_cohort)


# ---------------------------
# ANALYTICS
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
# ROUTING & FILTERS
# ---------------------------
if page == "Student Search":
    student_search(df)


    # ------------------ FILTERS ------------------
    
elif page == "Year 7 Passports":

    st.sidebar.subheader("🔎 Filters (Year 7)")

    form_groups = safe_unique(df, "Form Group")
    maths_sets = safe_unique(df, "Maths Set")

    selected_form = st.sidebar.multiselect(
        "Form Group (ALL by default)",
        form_groups,
        key="y7_form"
    )

    selected_math = st.sidebar.multiselect(
        "Maths Set (ALL by default)",
        maths_sets,
        key="y7_math"
    )

    filtered_df = df.copy()

    if selected_form:
        filtered_df = filtered_df[filtered_df["Form Group"].astype(str).isin(selected_form)]

    if selected_math:
        filtered_df = filtered_df[filtered_df["Maths Set"].astype(str).isin(selected_math)]

    render_y7_passports(filtered_df)

elif page == "Year 9 Transition":

    st.sidebar.subheader("🔎 Filters (Year 9)")

    form_groups = safe_unique(df, "Form Group")
    maths_sets = safe_unique(df, "Maths Set")

    selected_form = st.sidebar.multiselect(
        "Form Group (ALL by default)",
        form_groups,
        key="y9_form"
    )

    selected_math = st.sidebar.multiselect(
        "Maths Set (ALL by default)",
        maths_sets,
        key="y9_math"
    )

    # subject dropdown (optional)
    subject_cols = [
        "Eng Lang","Eng Lit","Maths","Science","Art","Computing","Design",
        "Drama","Geography","History","Hospitality","Music","Photography",
        "Spanish","Sport"
    ]

    available_subjects = [c for c in subject_cols if c in df.columns]

    selected_subject = st.sidebar.selectbox(
        "Subject (optional)",
        ["All Subjects"] + available_subjects,
        key="y9_subject"
    )

    filtered_df = df.copy()

    if selected_form:
        filtered_df = filtered_df[filtered_df["Form Group"].astype(str).isin(selected_form)]

    if selected_math:
        filtered_df = filtered_df[filtered_df["Maths Set"].astype(str).isin(selected_math)]

    if selected_subject != "All Subjects":
        filtered_df = filtered_df[
            filtered_df[selected_subject].notna() &
            (filtered_df[selected_subject].astype(str).str.strip() != "")
        ]

    render_y9_transition(filtered_df)

elif page == "Analytics":
    analytics(df)
    
