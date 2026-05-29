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
