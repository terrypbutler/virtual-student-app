import pandas as pd
import streamlit as st
from modules.ui_components import render_student_header, render_student_summary
from modules.helpers import get_header_title


# ---------------------------
# YEAR 7 PASSPORT REPORT
# ---------------------------
def render_y7_passports(filtered_df):
    st.subheader("📄 Year 7 Transition Passports")

    for _, row in filtered_df.iterrows():
        header = get_header_title(row, "Year 7 Passport")

        with st.container():
            render_student_header(row, "Year 7 Passport", "Year 7")

            st.write("---")
            render_student_summary(row)

            st.write("---")

            # Optional extra fields
            excluded = ["Full Name", "DoB"]
            extra_cols = [c for c in filtered_df.columns if c not in excluded]

            left_tab, right_tab = st.tabs(["General Info", "Additional Notes"])

            with left_tab:
                for col in extra_cols[:10]:
                    st.markdown(f"**{col}:** {row[col]}")

            with right_tab:
                for col in extra_cols[10:]:
                    st.markdown(f"**{col}:** {row[col]}")


# ---------------------------
# YEAR 7 SUBJECT REPORT
# ---------------------------
def render_subject_report(filtered_df):
    st.subheader("📊 Year 7 Academic Subject Reports")

    for _, row in filtered_df.iterrows():
        with st.container():
            render_student_header(row, "Academic Progress Report", "Year 7")
            st.write("---")

            metric1, metric2 = st.columns(2)
            metric1.metric("Current Grade", row.get("Current Grade", "N/A"))
            metric2.metric("Target Grade", row.get("Target Grade", "N/A"))
            st.write("---")

            render_student_summary(row)
            st.write("---")

            # Subject breakdown
            subject_data = {}
            for col in filtered_df.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in ["subject", "grade", "score"]) \
                        and not any(term in col_lower for term in ["target", "current", "maths", "reading"]):
                    subject_data[col] = row[col]

            if subject_data:
                summary_df = pd.DataFrame.from_dict(
                    subject_data,
                    orient="index",
                    columns=["Assigned Level / Progress Tracker"]
                )
                st.dataframe(summary_df, use_container_width=True)
            else:
                st.caption("*No subject performance data found*")


# ---------------------------
# YEAR 9 TRANSITION REPORT
# ---------------------------
def render_y9_transition(filtered_df):
    st.subheader("📁 Year 9 Transition Profiles")

    for _, row in filtered_df.iterrows():
        with st.container():
            render_student_header(row, "Year 9 Transition Profile", "Year 9")
            st.write("---")

            display_cols = [c for c in filtered_df.columns if c not in ["Full Name", "DoB"]]
            col1, col2 = st.columns(2)

            for i, col in enumerate(display_cols):
                target = col1 if i % 2 == 0 else col2
                target.markdown(f"**{col}:** {row[col]}")


# ---------------------------
# YEAR 9 FULL REPORT
# ---------------------------
def render_y9_full(filtered_df):
    st.subheader("💯 Full Year 9 Reports")

    for _, row in filtered_df.iterrows():
        with st.container():
            render_student_header(row, "Full Holistic Record", "Year 9")
            st.write("---")

            all_cols = [c for c in filtered_df.columns if c not in ["Full Name", "DoB"]]
            col1, col2, col3 = st.columns(3)

            for i, col in enumerate(all_cols):
                text = f"📌 **{col}:** {row[col]}"
                if i % 3 == 0:
                    col1.markdown(text)
                elif i % 3 == 1:
                    col2.markdown(text)
                else:
                    col3.markdown(text)
