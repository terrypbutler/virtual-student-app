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
    st.title("📊 MIS Cohort Intelligence Dashboard")

    st.markdown("Use filters to explore cohort performance and group-level patterns.")

    # ---------------------------
    # SIDEBAR FILTERS (INSIDE PAGE)
    # ---------------------------
    st.subheader("🎛 Filters")

    colA, colB, colC = st.columns(3)

    # Tutor / Form Group
    tutor_col = None
    for c in ["Tutor Group", "Form Group", "Form Tutor"]:
        if c in df.columns:
            tutor_col = c
            break

    if tutor_col:
        tutor_options = ["All"] + sorted(df[tutor_col].dropna().unique().tolist())
        selected_tutor = colA.selectbox("Tutor Group", tutor_options)
    else:
        selected_tutor = "All"

    # Metric selector
    metric_options = []
    if any(c in df.columns for c in ["SATs Maths", "SAT's Maths", "Maths Score"]):
        metric_options.append("Maths")
    if any(c in df.columns for c in ["SATs Reading", "SAT's Reading", "Reading Score"]):
        metric_options.append("Reading")

    selected_metric = colB.selectbox("Academic Metric", metric_options if metric_options else ["None"])

    # Grouping mode
    group_mode = colC.selectbox(
        "Group By",
        ["Whole Cohort", "Tutor Group", "SEN Status", "EAL"]
    )

    st.write("---")

    # ---------------------------
    # FILTER DATASET
    # ---------------------------
    filtered = df.copy()

    if tutor_col and selected_tutor != "All":
        filtered = filtered[filtered[tutor_col] == selected_tutor]

    # ---------------------------
    # METRIC COLUMN RESOLUTION
    # ---------------------------
    metric_col = None

    if selected_metric == "Maths":
        for c in ["SATs Maths", "SAT's Maths", "Maths Score"]:
            if c in df.columns:
                metric_col = c
                break

    elif selected_metric == "Reading":
        for c in ["SATs Reading", "SAT's Reading", "Reading Score"]:
            if c in df.columns:
                metric_col = c
                break

    # ---------------------------
    # 1️⃣ OVERVIEW METRICS
    # ---------------------------
    st.subheader("📌 Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric("Students", len(filtered))

    if "SEN Status" in filtered.columns:
        sen_count = (filtered["SEN Status"].fillna("").str.lower() != "").sum()
        c2.metric("SEN Students", sen_count)

    if "EAL" in filtered.columns:
        eal_count = (filtered["EAL"].fillna("").str.lower() != "").sum()
        c3.metric("EAL Students", eal_count)

    st.write("---")

    # ---------------------------
    # 2️⃣ GROUPED PERFORMANCE CHART
    # ---------------------------
    st.subheader("📊 Group Performance Comparison")

    if metric_col:
        if group_mode == "Whole Cohort":
            st.bar_chart(filtered[metric_col].value_counts().sort_index())

        elif group_mode == "Tutor Group" and tutor_col:
            grouped = filtered.groupby(tutor_col)[metric_col].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            )
            st.bar_chart(grouped)

        elif group_mode == "SEN Status" and "SEN Status" in filtered.columns:
            grouped = filtered.groupby("SEN Status")[metric_col].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            )
            st.bar_chart(grouped)

        elif group_mode == "EAL" and "EAL" in filtered.columns:
            grouped = filtered.groupby("EAL")[metric_col].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            )
            st.bar_chart(grouped)
    else:
        st.info("No valid academic metric found for this cohort.")

    st.write("---")

    # ---------------------------
    # 3️⃣ DISTRIBUTION VIEW (SEN / EAL / PP)
    # ---------------------------
    st.subheader("🔹 Cohort Profile Breakdown")

    breakdown = {}

    if "SEN Status" in filtered.columns:
        breakdown["SEN"] = (filtered["SEN Status"].fillna("") != "").sum()

    if "EAL" in filtered.columns:
        breakdown["EAL"] = (filtered["EAL"].fillna("") != "").sum()

    for c in ["Pupil Premium", "Disadvantaged (PP)", "Premium"]:
        if c in filtered.columns:
            breakdown["PP"] = (filtered[c].fillna("") != "").sum()
            break

    if breakdown:
        st.bar_chart(pd.Series(breakdown))

    st.write("---")

    # ---------------------------
    # 4️⃣ RAW INSPECTOR (MIS STYLE)
    # ---------------------------
    st.subheader("🔍 Data Inspector")

    st.dataframe(filtered, use_container_width=True)
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
