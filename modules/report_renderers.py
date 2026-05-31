import streamlit as st
from modules.ui_components import render_student_header, render_student_summary
from modules.photo_utils import display_student_photo
from modules.helpers import get_field

def get_flexible_text(row, possible_names):
    """Helper to find columns even if they have hidden spaces or weird capitalization."""
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.lower() not in ["nan", "none", "n/a", ""]:
                return val
    return None

def render_student_card(row, cohort, show_subjects=False, show_projected=True, y7_report_type="None"):
    """
    Master rendering function. Adapts to Y7/Y10 and specific report requirements.
    """
    name = row.get("Full Name", "Unknown")
    
    with st.expander(f"👤 {name}"):
        # 1. Header & Photo
        render_student_header(row, title=f"{cohort} Profile", cohort=cohort)
        
        st.divider()
        
        # 2. Summary Table
        render_student_summary(row)
        
        # 3. Projected Grades
        if show_projected:
            proj = str(row.get("Projected Grade", "")).strip()
            if proj and proj.lower() != "nan":
                st.info(f"**Projected Grade:** {proj}")
                
        # --- 4. YEAR 7 CUSTOM REPORTS ---
        if cohort == "Year 7" and y7_report_type != "None":
            st.divider()
            st.markdown(f"### 📑 {y7_report_type} Report")
            
            portrait = get_flexible_text(row, ["Transition Portrait", "Transition portrait", "Portrait"])
            if portrait:
                st.markdown("**Transition Portrait:**")
                st.write(portrait)
            else:
                st.caption("*(No Transition Portrait data found in spreadsheet)*")
                
            home_life = get_flexible_text(row, ["Home Life & Interests", "Home Life", "Home life & interests", "Interests"])
            if home_life:
                st.markdown("**Home Life & Interests:**")
                st.write(home_life)
            else:
                st.caption("*(No Home Life data found in spreadsheet)*")
                
            if y7_report_type == "Detailed":
                st.markdown("**Subject Overviews:**")
                y7_subjects = ["Maths", "English", "Creative Arts", "PE", "Sciences", "Science", "Humanities"]
                
                available_y7 = {}
                row_keys_lower = {str(k).strip().lower(): k for k in row.keys()}
                
                for sub in y7_subjects:
                    sub_clean = sub.lower()
                    if sub_clean in row_keys_lower:
                        actual_key = row_keys_lower[sub_clean]
                        val = str(row[actual_key]).strip()
                        if val and val.lower() not in ["nan", "none", "n/a", ""]:
                            available_y7[sub] = val
                
                if available_y7:
                    st.table(available_y7)
                else:
                    st.caption("*(No subject data found for this student)*")

        # --- 5. YEAR 10 SUBJECT REPORTS ---
        elif show_subjects and cohort == "Year 10":
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
                st.caption("*(No subject data available)*")


def render_photo_grid(df, cohort, num_cols=5):
    """
    Renders a strict grid of student photos with key demographic details.
    """
    if df.empty:
        st.warning("No students found for this selection.")
        return

    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN"]

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

    st.markdown("### 📊 Selection Overview")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", len(df))
    m2.metric("SEN Support", sen_count)
    m3.metric("EAL", eal_count)
    m4.metric("Pupil Premium", pp_count)

    st.write("---") 

    for i in range(0, len(df), num_cols):
        cols = st.columns(num_cols)
        row_students = df.iloc[i : i + num_cols]
        
        for col, (_, row) in zip(cols, row_students.iterrows()):
            with col:
                name = row.get("Full Name", "Unknown")
                
                sen_status = str(get_field(row, "sen_status")).strip()
                sen_detail = str(get_field(row, "sen_detail")).strip()
                pp_status = str(get_field(row, "pp")).strip()
                eal_status = str(get_field(row, "eal")).strip()
                
                sen_active = sen_status.upper() not in ignore_list
                pp_active = pp_status.upper() not in ignore_list
                eal_active = eal_status.upper() not in ignore_list
                
                display_student_photo(name, cohort)
                st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: 2px;'>{name}</p>", unsafe_allow_html=True)
                
                active_labels = []
                if sen_active:
                    detail_str = f" ({sen_detail})" if sen_detail.upper() not in ignore_list else ""
                    active_labels.append(f"<span style='color: #D32F2F; font-weight: bold;'>{sen_status}{detail_str}</span>")
                if pp_active:
                    active_labels.append("<span style='color: #1976D2; font-weight: bold;'>PP</span>")
                if eal_active:
                    active_labels.append(f"<span style='color: #388E3C; font-weight: bold;'>EAL: {eal_status}</span>")
                
                if active_labels:
                    labels_combined = "<br>".join(active_labels)
                    details_html = f"""
                    <div style='text-align: center; font-size: 0.8em; line-height: 1.4; padding-bottom: 10px;'>
                        {labels_combined}
                    </div>
                    """
                    st.markdown(details_html, unsafe_allow_html=True)
        
        st.write("---")
