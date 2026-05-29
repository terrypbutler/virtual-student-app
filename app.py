import streamlit as st
import pandas as pd

from modules.data_loader import load_data
from modules.report_renderers import (
    render_y7_passports,
    render_subject_report,
    render_y9_transition,
    render_y9_full
)

# Optional analytics import (only used on page)
import matplotlib.pyplot as plt


# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="Virtual Student MIS", layout="wide")


# ---------------------------
# DATA SOURCES
# ---------------------------
YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"


# ---------------------------
# LOAD DATA (CACHED IN MODULE)
# ---------------------------
selected_cohort = st.sidebar.radio("📅 Cohort", ["Year 7", "Year 9"])

df = load_data(YEAR_7_URL if selected_cohort == "Year 7" else YEAR_9_URL)


# ---------------------------
# SIDEBAR NAVIGATION
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
# STUDENT SEARCH
# ---------------------------
def student_search(df):
    st.title("🔍 Student Search")

    query = st.text_input("Search by student name")

    if query:
        results = df[df["Full Name"].str.contains(query, case=False, na=False)]

        st.write(f"Found {len(results)} students")

        for _, row in results.iterrows():
            st.markdown(f"### {row['Full Name']}")
            st.write(row.to_dict())
            st.write("---")


# ---------------------------
# ANALYTICS
# ---------------------------
def analytics(df):
    st.title("📊 Cohort Analytics")

    col1, col2 = st.columns(2)

    with col1:
        if "SEN Status" in df.columns:
            st.subheader("SEN Distribution")
            fig, ax = plt.subplots()
            df["SEN Status"].value_counts().plot(kind="bar", ax=ax)
            st.pyplot(fig)

    with col2:
        if "EAL" in df.columns:
            st.subheader("EAL Distribution")
            fig, ax = plt.subplots()
            df["EAL"].value_counts().plot(kind="bar", ax=ax)
            st.pyplot(fig)

def analytics(df):
    st.title("📊 Cohort Analytics Dashboard")

    st.markdown("Visualize your cohort: SEN, EAL, Disadvantaged, and Academic Performance.")

    # Make sure necessary columns exist
    sen_col = "SEN Status" if "SEN Status" in df.columns else None
    eal_col = "EAL" if "EAL" in df.columns else None
    pp_col = None
    for c in ["Pupil Premium", "Disadvantaged (PP)", "Premium"]:
        if c in df.columns:
            pp_col = c
            break
    maths_col = None
    for c in ["SATs Maths", "SAT's Maths", "Maths Score"]:
        if c in df.columns:
            maths_col = c
            break
    tutor_col = None
    for c in ["Tutor Group", "Form Group", "Form Tutor"]:
        if c in df.columns:
            tutor_col = c
            break

    # -------------------------------
    # 1️⃣ Stacked Bar: SEN / EAL / PP
    # -------------------------------
    st.subheader("🔹 SEN / EAL / Disadvantaged (PP) Distribution")

    if sen_col or eal_col or pp_col:
        stacked_df = pd.DataFrame()

        if sen_col:
            stacked_df["SEN"] = df[sen_col].fillna("None").map(lambda x: 1 if x not in ["", "None", "No"] else 0)
        if eal_col:
            stacked_df["EAL"] = df[eal_col].fillna("No").map(lambda x: 1 if x not in ["", "No"] else 0)
        if pp_col:
            stacked_df["PP"] = df[pp_col].fillna("No").map(lambda x: 1 if x not in ["", "No"] else 0)

        st.bar_chart(stacked_df.sum())

    else:
        st.info("SEN, EAL or Pupil Premium columns not found in this dataset.")

    st.write("---")

    # -------------------------------
    # 2️⃣ Maths Grade Distribution Histogram
    # -------------------------------
    if maths_col:
        st.subheader("🔹 Maths Grade Distribution")
        grades = df[maths_col].dropna().astype(str)

        # convert grades to numeric if possible, else use string counts
        try:
            grades_numeric = pd.to_numeric(grades, errors="coerce").dropna()
            st.bar_chart(grades_numeric.value_counts().sort_index())
        except:
            st.bar_chart(grades.value_counts().sort_index())
    else:
        st.info("Maths grade column not found in this dataset.")

    st.write("---")

    # -------------------------------
    # 3️⃣ Tutor Group Comparison
    # -------------------------------
    if tutor_col and maths_col:
        st.subheader("🔹 Maths Performance by Tutor Group")
        tutor_perf = df.groupby(tutor_col)[maths_col].apply(lambda x: pd.to_numeric(x, errors="coerce").mean())
        st.bar_chart(tutor_perf)
    else:
        st.info("Tutor group or Maths column missing — cannot compare groups.")
# ---------------------------
# ROUTING SYSTEM
# ---------------------------

if page == "Student Search":
    student_search(df)

elif page == "Year 7 Passports":
    st.title("📄 Year 7 Passports")
    render_y7_passports(df)

elif page == "Year 7 Reports":
    st.title("📊 Year 7 Reports")
    render_subject_report(df)

elif page == "Year 9 Transition":
    st.title("📁 Year 9 Transition Profiles")
    render_y9_transition(df)

elif page == "Year 9 Full Reports":
    st.title("💯 Year 9 Full Reports")
    render_y9_full(df)

elif page == "Analytics":
    analytics(df)
