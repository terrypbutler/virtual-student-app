import streamlit as st
import pandas as pd
from modules.data_loader import load_data
from modules.report_renderers import render_student_card, render_photo_grid

def safe_unique(df, col):
    if col in df.columns:
        return sorted(df[col].dropna().astype(str).unique().tolist())
    return []

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Butler Academy MIS", layout="wide")

YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"
YEAR_10_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"

# ---------------------------
# DATA LOAD
# ---------------------------
df_y7 = load_data(YEAR_7_URL)
df_y10 = load_data(YEAR_10_URL)

# ---------------------------
# SIDEBAR NAV
# ---------------------------
st.sidebar.title("🎓 Butler Academy")

page = st.sidebar.radio(
    "Navigate",
    [
        "Student Search",
        "Year 7",
        "Year 10",
        "Analytics"
    ],
    key="sidebar_nav"
)

# ---------------------------
# SEARCH PAGE
# ---------------------------
def student_search(df_y7, df_y10):
    st.title("🔍 Student Search (MIS View)")
    
    search_cohort = st.radio("Select Cohort to Search:", ["Year 7", "Year 10"], horizontal=True)
    
    df = df_y7 if search_cohort == "Year 7" else df_y10

    query = st.text_input("Search student name", key="search_name")

    if query:
        results = df[df["Full Name"].str.contains(query, case=False, na=False)]
        st.write(f"Found {len(results)} students")

        if len(results) == 0:
            st.warning("No matches found.")

        for _, row in results.iterrows():
            # Force Detailed report on search so teachers see everything
            render_student_card(row, search_cohort, show_projected=True, report_type="Detailed")

# ---------------------------
# ANALYTICS
# ---------------------------
def analytics(df_y7, df_y10):
    st.title("📊 Cohort Analytics Dashboard")

    analytics_cohort = st.radio("Select Cohort to Analyze:", ["Year 7", "Year 10"], horizontal=True)
    df = df_y7 if analytics_cohort == "Year 7" else df_y10

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
    student_search(df_y7, df_y10)

# ------------------ YEAR 7 ------------------
elif page == "Year 7":
    df = df_y7 
    
    st.sidebar.subheader("🔎 Filters (Year 7)")

    form_groups = safe_unique(df, "Form Group")
    maths_sets = safe_unique(df, "Maths Set")

    selected_form = st.sidebar.multiselect("Form Group (ALL by default)", form_groups, key="y7_form")
    selected_math = st.sidebar.multiselect("Maths Set (ALL by default)", maths_sets, key="y7_math")

    filtered_df = df.copy()

    if selected_form:
        filtered_df = filtered_df[filtered_df["Form Group"].astype(str).isin(selected_form)]
    if selected_math:
        filtered_df = filtered_df[filtered_df["Maths Set"].astype(str).isin(selected_math)]

    report_option = st.sidebar.radio(
        "Select Report Detail",
        ["Base Passport (No Details)", "Short Report (Portrait & Home Life)", "Detailed Report (All Subjects)"]
    )

    mode = "None"
    if report_option == "Short Report (Portrait & Home Life)":
        mode = "Short"
    elif report_option == "Detailed Report (All Subjects)":
        mode = "Detailed"

    st.subheader(f"Showing {len(filtered_df)} Students")
    
    render_photo_grid(filtered_df, "Year 7", num_cols=5)
    
    st.divider()
    st.subheader("📄 Detailed Passports")
    
    for _, row in filtered_df.iterrows():
        render_student_card(row, "Year 7", show_projected=True, report_type=mode)

# ------------------ YEAR 10 ------------------
elif page == "Year 10":
    df = df_y10 
    
    st.sidebar.subheader("🔎 Filters (Year 10)")

    form_groups = safe_unique(df, "Form Group")
    maths_sets = safe_unique(df, "Maths Set")

    selected_form = st.sidebar.multiselect("Form Group (ALL by default)", form_groups, key="y10_form")
    selected_math = st.sidebar.multiselect("Maths Set (ALL by default)", maths_sets, key="y10_math")

    subject_cols = [
        "Eng Lang","Eng Lit","Maths","Science","Art","Computing","Design",
        "Drama","Geography","History","Hospitality","Music","Photography",
        "Spanish","Sport"
    ]

    available_subjects = [c for c in subject_cols if c in df.columns]

    selected_subject = st.sidebar.selectbox("Subject (optional)", ["All Subjects"] + available_subjects, key="y10_subject")

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

    # New 3-tier selector for Year 10
    report_option = st.sidebar.radio(
        "Select Report Detail",
        ["Base Passport (No Details)", "Short Report (KS3 & Home Life)", "Detailed Report (All Subjects)"]
    )

    mode = "None"
    if report_option == "Short Report (KS3 & Home Life)":
        mode = "Short"
    elif report_option == "Detailed Report (All Subjects)":
        mode = "Detailed"

    st.subheader(f"Showing {len(filtered_df)} Students")
    
    render_photo_grid(filtered_df, "Year 10", num_cols=5)
    
    st.divider()
    st.subheader("📄 Detailed Passports")
    
    for _, row in filtered_df.iterrows():
        render_student_card(row, "Year 10", show_projected=True, report_type=mode)

# ------------------ ANALYTICS ------------------
elif page == "Analytics":
    analytics(df_y7, df_y10)
    
