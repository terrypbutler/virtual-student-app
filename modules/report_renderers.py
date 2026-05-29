import streamlit as st
from modules.ui_components import render_student_header, render_student_summary
from modules.photo_utils import display_student_photo
from modules.helpers import get_field

def render_student_card(row, cohort, show_subjects=False, show_projected=True):
    """
    Master rendering function. Adapts to Y7/Y9 and specific report requirements.
    """
    name = row.get("Full Name", "Unknown")
    
    with st.expander(f"👤 {name}"):
        # 1. Header & Photo (from ui_components)
        render_student_header(row, title=f"{cohort} Profile", cohort=cohort)
        
        st.divider()
        
        # 2. Summary Table (from ui_components)
        render_student_summary(row)
        
        # 3. Projected Grades (Toggleable)
        if show_projected:
            proj = str(row.get("Projected Grade", "")).strip()
            if proj and proj.lower() != "nan":
                st.info(f"**Projected Grade:** {proj}")
                
        # 4. Subject Reports (Toggleable)
        if show_subjects:
            st.subheader("Subject Reports")
            subject_cols = [
                "Eng Lang","Eng Lit","Maths","Science","Art","Computing",
                "Design","Drama","Geography","History","Hospitality","Music",
                "Photography","Spanish","Sport"
            ]
            available = {
                sub: row[sub] for sub in subject_cols 
                if sub in row.index and str(row[sub]).strip() and str(row[sub]).strip().lower() != "nan"
            }
            
            if available:
                st.table(available)
            else:
                st.caption("No subject data available.")

def render_photo_grid(df, cohort, num_cols=5):
    """
    Renders a strict grid of student photos with key demographic details.
    Includes a metrics dashboard at the top for quick cohort analysis.
    """
    if df.empty:
        st.warning("No students found for this selection.")
        return

    # --- 1. CALCULATE COHORT STATS ---
    sen_count = 0
    eal_count = 0
    pp_count = 0

    # Negative words to ignore when counting flags
    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE"]

    for _, row in df.iterrows():
        if str(get_field(row, "sen_status")).strip().upper() not in ignore_list:
            sen_count += 1
        if str(get_field(row, "eal")).strip().upper() not in ignore_list:
            eal_count += 1
        if str(get_field(row, "pp")).strip().upper() not in ignore_list:
            pp_count += 1

    # --- 2. RENDER METRICS DASHBOARD ---
    st.markdown("### 📊 Selection Overview")
    
    # Create 4 equal columns for the top metrics
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("Total Students", len(df))
    m2.metric("SEN Support", sen_count)
    m3.metric("EAL", eal_count)
    m4.metric("Pupil Premium", pp_count)

    st.write("---") # Thick divider before the photos start

    # --- 3. RENDER PHOTO GRID ---
    # Loop through the dataframe in chunks to create strict horizontal rows
    for i in range(0, len(df), num_cols):
        cols = st.columns(num_cols)
        row_students = df.iloc[i : i + num_cols]
        
        for col, (_, row) in zip(cols, row_students.iterrows()):
            with col:
                name = row.get("Full Name", "Unknown")
                
                sen_status = get_field(row, "sen_status")
                sen_detail = get_field(row, "sen_detail")
                pp_status = get_field(row, "pp")
                eal_status = get_field(row, "eal")
                
                display_student_photo(name, cohort)
                
                st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: 2px;'>{name}</p>", unsafe_allow_html=True)
                
                details_html = f"""
                <div style='text-align: center; font-size: 0.8em; color: #555; line-height: 1.3;'>
                    <strong>SEN:</strong> {sen_status}<br>
                    <strong>Detail:</strong> {sen_detail}<br>
                    <strong>PP:</strong> {pp_status} | <strong>EAL:</strong> {eal_status}
                </div>
                """
                st.markdown(details_html, unsafe_allow_html=True)
        
        st.write("---")
