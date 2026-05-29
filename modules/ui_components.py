# modules/ui_components.py

import streamlit as st

from modules.helpers import get_field


def render_student_summary(row):
    summary = {
        "Form Group": get_field(row, "form_group"),
        "Gender": get_field(row, "gender"),
        "SEN Status": get_field(row, "sen_status"),
        "SEND Detail": get_field(row, "sen_detail"),
        "Ethnicity": get_field(row, "ethnicity"),
        "EAL": get_field(row, "eal"),
        "Disadvantaged": get_field(row, "pp"),
        "SATs Reading": get_field(row, "reading"),
        "SATs Maths": get_field(row, "maths")
    }

    col1, col2 = st.columns(2)

    items = list(summary.items())

    for i, (key, value) in enumerate(items):
        target = col1 if i % 2 == 0 else col2
        target.markdown(f"**{key}:** {value}")



def render_student_header(row, title):
    name = row.get("Full Name", "Unknown Student")
    dob = row.get("DoB", "")

    left, right = st.columns([3, 1])

    with left:
        if dob:
            st.markdown(f"### {title}: {name} ({dob})")
        else:
            st.markdown(f"### {title}: {name}")

    with right:
        from modules.photo_utils import display_student_photo
        display_student_photo(name)
