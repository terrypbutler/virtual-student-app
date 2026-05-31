import streamlit as st
import pandas as pd
from modules.photo_utils import display_student_photo

def get_flexible_text(row, possible_names):
    """Helper to find columns and strip out N/A values completely."""
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                if val.endswith(".0"):
                    val = val[:-2]
                return val
    return None

def render_student_card(row, cohort, show_projected=True, report_type="None", is_print_mode=False):
    """
    Master rendering function. Adapts to Y7/Y10 and specific 3-tier report requirements.
    Added is_print_mode to force expanders open for PDF printing.
    """
    name = row.get("Full Name", "Unknown")
    
    # If print mode is on, force the expander open!
    with st.expander(f"👤 {name}", expanded=is_print_mode):
        
        # --- 1. HEADER & SUMMARY DASHBOARD ---
        left, right = st.columns([3, 1])
        
        with left:
            st.markdown(f"### {cohort} Profile")
            
            def get_val(keys):
                for k in keys:
                    for row_key in row.keys():
                        if str(row_key).strip().lower() == str(k).strip().lower():
                            val = str(row[row_key]).strip()
                            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL"]:
                                if val.endswith(".0"):
                                    val = val[:-2]
                                if "attendance" in str(k).lower() and "%" not in val:
                                    val = f"{val}%"
                                return val
                return ""

            info = {
                "Form Group": ["Form Tutor", "Tutor", "Form Group"],
                "Gender": ["Gender"],
                "Attendance": ["Attendance %", "Attendance"],
                "Suspensions": ["Suspension days", "Suspensions", "Suspension Days"],
                "SEN Status": ["SEN Status", "SEND Status"],
                "SEN Detail": ["SEN detail", "SEND detail"],
                "Ethnicity": ["Ethnicity"],
                "EAL": ["EAL", "EAL Status"],
                "Disadvantaged": ["Disadvantaged (PP)", "Premium", "Disadvantaged", "Pupil Premium", "PP"],
                "KS2 Reading": ["KS2 Read", "KS2 Reading", "SATs Reading"], 
                "KS2 Maths": ["KS2 Maths", "KS2 Math", "SATs Maths"]        
            }

            cols = st.columns(2)
            items = list(info.items())
            for i, (label, keys) in enumerate(items):
                value = get_val(keys)
                
                html_card = f"""
                <div style='margin-bottom: 12px; line-height: 1.3;'>
                    <span style='font-size: 0.85em; opacity: 0.7;'>{label}</span><br>
                    <span style='font-size: 1.1em; font-weight: 600; display: inline-block; word-wrap: break-word;'>{value}</span>
                </div>
                """
                cols[i % 2].markdown(html_card, unsafe_allow_html=True)
                
        with right:
            display_student_photo(name, cohort)
            
        st.divider()
        
        if show_projected:
            proj = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
            if proj:
                st.info(f"**Overall Projected Grade:** {proj}")
                
        # --- 4. YEAR 7 CUSTOM REPORTS ---
        if cohort == "Year 7" and report_type != "None":
            st.divider()
            st.markdown(f"### 📑 {report_type} Report")
            
            portrait = get_flexible_text(row, ["Transition Portrait", "Transition portrait", "Portrait"])
            if portrait:
                st.markdown("**Transition Portrait:**")
                st.write(portrait)
            elif report_type == "Detailed":
                st.caption("*(No Transition Portrait data found in spreadsheet)*")
                
            home_life = get_flexible_text(row, ["Home Life & Interests", "Home Life", "Home life & interests", "Interests"])
            if home_life:
                st.markdown("**Home Life & Interests:**")
                st.write(home_life)
            elif report_type == "Detailed":
                st.caption("*(No Home Life data found in spreadsheet)*")
                
            if report_type == "Detailed":
                st.markdown("**Subject Overviews:**")
                y7_subjects = ["Maths", "English", "Creative Arts", "PE", "Sciences", "Science", "Humanities"]
                
                available_y7 = {}
                for sub in y7_subjects:
                    val = get_flexible_text(row, [sub])
                    if val:
                        available_y7[sub] = val
                
                if available_y7:
                    st.table(available_y7)

        # --- 5. YEAR 10 CUSTOM REPORTS ---
        elif cohort == "Year 10" and report_type != "None":
            st.divider()
            st.markdown(f"### 📑 {report_type} Report")

            ks3_report = get_flexible_text(row, ["Key Stage 3 Report", "KS3 Report", "Key Stage 3"])
            if ks3_report:
                st.markdown("**Key Stage 3 Report:**")
                st.write(ks3_report)
            elif report_type == "Detailed":
                st.caption("*(No Key Stage 3 Report data found in spreadsheet)*")

            home_life = get_flexible_text(row, ["Home Life & Interests", "Home Life", "Home life & interests", "Interests"])
            if home_life:
                st.markdown("**Home Life & Interests:**")
                st.write(home_life)
            elif report_type == "Detailed":
                st.caption("*(No Home Life data found in spreadsheet)*")

            if report_type == "Detailed":
                st.markdown("**Subject Overviews:**")
                subject_cols = [
                    "Eng Lang","Eng Lit","Maths","Science","Art","Computing",
                    "Design","Drama","Geography","History","Hospitality","Music",
                    "Photography","Spanish","Sport"
                ]
                
                table_data = []
                global_pred = get_flexible_text(row, ["Projected Grade", "Predicted Grade"]) or ""
                
                for sub in subject_cols:
                    grade = get_flexible_text(row, [sub])
                    
                    if grade: 
                        if sub.lower() == "science":
                            sci1 = get_flexible_text(row, ["Sci 1 Predicted Grade", "Sci 1 Predicted"])
                            sci2 = get_flexible_text(row, ["Sci 2 Predicted Grade", "Sci 2 Predicted"])
                            
                            if sci1 and sci2:
                                sub_pred = f"{sci1}-{sci2}"
                            elif sci1:
                                sub_pred = sci1
                            elif sci2:
                                sub_pred = sci2
                            else:
                                sub_pred = get_flexible_text(row, ["Science Predicted Grade", "Science Predicted"])
                        else:
                            sub_pred = get_flexible_text(row, [f"{sub} Predicted Grade", f"{sub} Predicted", f"Predicted {sub}"])
                        
                        final_pred = sub_pred if sub_pred else global_pred
                        
                        table_data.append({
                            "Subject": sub,
                            "Current Grade": grade,
                            "Predicted Grade": final_pred
                        })
                
                if table_data:
                    df_subjects = pd.DataFrame(table_data)
                    st.table(df_subjects.set_index("Subject"))

def render_photo_grid(df, cohort, num_cols=5):
    """
    Renders a strict grid of student photos with key demographic details.
    """
    if df.empty:
        st.warning("No students found for this selection.")
        return

    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN", "0", "0.0"]

    sen_count = 0
    eal_count = 0
    pp_count = 0

    for _, row in df.iterrows():
        sen_val = get_flexible_text(row, ["SEN Status", "SEND Status"]) or ""
        eal_val = get_flexible_text(row, ["EAL", "EAL Status"]) or ""
        pp_val = get_flexible_text(row, ["Disadvantaged (PP)", "Disadvantaged", "Pupil Premium", "PP", "Premium"]) or ""
        
        if sen_val.upper() not in ignore_list:
            sen_count += 1
        if eal_val.upper() not in ignore_list:
            eal_count += 1
        if pp_val.upper() not in ignore_list:
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
                
                sen_status = get_flexible_text(row, ["SEN Status", "SEND Status"]) or ""
                sen_detail = get_flexible_text(row, ["SEN detail", "SEND detail"]) or ""
                eal_status = get_flexible_text(row, ["EAL", "EAL Status"]) or ""
                pp_status = get_flexible_text(row, ["Disadvantaged (PP)", "Disadvantaged", "Pupil Premium", "PP", "Premium"]) or ""
                
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
