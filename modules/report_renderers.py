import pandas as pd
import streamlit as st

from modules.ui_components import (
    render_student_header,
    render_student_summary
)

from modules.helpers import get_header_title


def render_y7_passports(filtered_df):
    st.subheader("📄 Year 7 Transition Passports")

    for _, row in filtered_df.iterrows():
        header = get_header_title(row, "Year 7 Passport")

        with st.container():
            st.markdown(f"## {header}")

            render_student_header(row, "Student Passport")
            st.write("---")

            render_student_summary(row)
            st.write("---")

            excluded = ["Full Name", "DoB"]
            extra_cols = [c for c in filtered_df.columns if c not in excluded]

            tab1, tab2 = st.tabs(["General Information", "Additional Notes"])

            with tab1:
                for col in extra_cols[:10]:
                    st.markdown(f"**{col}:** {row[col]}")

            with tab2:
                for col in extra_cols[10:]:
                    st.markdown(f"**{col}:** {row[col]}")


def render_subject_report(filtered_df):
    st.subheader("📊 Academic Subject Reports")

    for _, row in filtered_df.iterrows():
        with st.container():
            render_student_header(row, "Academic Progress Report")
            st.write("---")

            metric1, metric2 = st.columns(2)
            metric1.metric("Current Grade", row.get("Current Grade", "N/A"))
            metric2.metric("Target Grade", row.get("Target Grade", "N/A"))
            st.write("---")

            render_student_summary(row)
            st.write("---")

            subject_data = {}
            for col in filtered_df.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in ["subject", "grade", "score"]):
                    subject_data[col] = row[col]

            if subject_data:
                summary_df = pd.DataFrame.from_dict(
                    subject_data,
                    orient="index",
                    columns=["Result"]
                )
                st.dataframe(summary_df, use_container_width=True)
