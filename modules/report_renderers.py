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
    Includes a metrics dashboard and conditional color-coding for SEN/PP/EAL.
    """
    if df.empty:
        st.warning("No students found for this selection.")
        return

    # Negative words to ignore when counting/highlighting flags
    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN"]

    # --- 1. CALCULATE COHORT STATS ---
    sen_count = 0
    eal_count = 0
    pp_count = 0

    for _, row in df.iterrows():
        if str(get_field(row, "sen_status")).strip().upper() not in ignore_list:
            sen_count += 1
        if str(get_field(row, "eal")).strip().upper() not in ignore_list:
            eal_count += 1
        if str(get_field(row, "pp")).strip().upper() not in ignore_list:
            pp_count += 1

    # --- 2. RENDER METRICS DASHBOARD ---
    st.markdown("### 📊 Selection Overview")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", len(df))
    m2.metric("SEN Support", sen_count)
    m3.metric("EAL", eal_count)
    m4.metric("Pupil Premium", pp_count)

    st.write("---") 

    # --- 3. RENDER PHOTO GRID ---
    for i in range(0, len(df), num_cols):
        cols = st.columns(num_cols)
        row_students = df.iloc[i : i + num_cols]
        
        for col, (_, row) in zip(cols, row_students.iterrows()):
            with col:
                name = row.get("Full Name", "Unknown")
                
                # Extract raw values
                sen_status = get_field(row, "sen_status")
                sen_detail = get_field(row, "sen_detail")
                pp_status = get_field(row, "pp")
                eal_status = get_field(row, "eal")
                
                # Check if flags are active
                sen_active = str(sen_status).strip().upper() not in ignore_list
                pp_active = str(pp_status).strip().upper() not in ignore_list
                eal_active = str(eal_status).strip().upper() not in ignore_list
                
                # Render Photo and Name
                display_student_photo(name, cohort)
                st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: 2px;'>{name}</p>", unsafe_allow_html=True)
                
                # --- CONDITIONAL COLOR FORMATTING ---
                # SEN logic: Red, Bold, include detail if active
                if sen_active:
                    sen_html = f"<span style='color: #D32F2F; font-weight: bold;'>SEN: {sen_status} ({sen_detail})</span>"
                else:
                    sen_html = f"SEN: {sen_status}"
                    
                # PP logic: Blue if active
                if pp_active:
                    pp_html = f"<span style='color: #1976D2; font-weight: bold;'>PP: {pp_status}</span>"
                else:
                    pp_html = f"PP: {pp_status}"
                    
                # EAL logic: Green if active
                if eal_active:
                    eal_html = f"<span style='color: #388E3C; font-weight: bold;'>EAL: {eal_status}</span>"
                else:
                    eal_html = f"EAL: {eal_status}"
                
# Combine into final HTML block
                details_html = f"""
                <div style='text-align: center; font-size: 0.8em; color: #555; line-height: 1.4; padding-bottom: 10px;'>
                    {sen_html}<br>
                    {pp_html}<br>
                    {eal_html}
                </div>
                """
                st.markdown(details_html, unsafe_allow_html=True)
        
        st.write("---")
