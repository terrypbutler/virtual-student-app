# app.py

import streamlit as st

from config import YEAR_7_URL, YEAR_9_URL

from modules.data_loader import load_data

from modules.report_renderers import (
    render_y7_passports,
    render_subject_report
)


st.set_page_config(
    page_title="Virtual Student Intake Dashboard",
    layout="wide"
)

st.title("🎓 Virtual Student Intake Dashboard")

st.sidebar.header("Navigation")

selected_cohort = st.sidebar.radio(
    "Select Cohort",
    ["Year 7", "Year 9"]
)

view_type = st.sidebar.radio(
    "Group By",
    ["Maths Set", "Tutor Group"]
)

if selected_cohort == "Year 7":
    df = load_data(YEAR_7_URL)
else:
    df = load_data(YEAR_9_URL)

# Search
search_term = st.sidebar.text_input("Search Student")

if search_term:
    df = df[
        df["Full Name"]
        .astype(str)
        .str.contains(search_term, case=False)
    ]


# Dynamic grouping
if view_type == "Maths Set":
    target_column = "Maths Set"
else:
    target_column = "Tutor Group"


if target_column in df.columns:
    groups = sorted(df[target_column].dropna().unique())

    selected_group = st.sidebar.selectbox(
        f"Select {view_type}",
        groups
    )

    filtered_df = df[
        df[target_column] == selected_group
    ]

else:
    filtered_df = df

# Dashboard metrics
metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Students Loaded",
    len(filtered_df)
)

metric2.metric(
    "EAL Students",
    len(filtered_df[
        filtered_df.astype(str)
        .apply(lambda row: row.str.contains("EAL", case=False).any(), axis=1)
    ])
)

metric3.metric(
    "SEN Students",
    len(filtered_df[
        filtered_df.astype(str)
        .apply(lambda row: row.str.contains("SEN", case=False).any(), axis=1)
    ])
)


st.write("---")


report_type = st.radio(
    "Select Report",
    [
        "Year 7 Passports",
        "Academic Subject Reports"
    ],
    horizontal=True
)


if report_type == "Year 7 Passports":
    render_y7_passports(filtered_df)

elif report_type == "Academic Subject Reports":
    render_subject_report(filtered_df)
