import streamlit as st
import pandas as pd
from modules.photo_utils import display_student_photo
from modules.helpers import get_field

def get_flexible_text(row, possible_names):
    """Helper to find columns and strip out N/A values completely."""
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            # If the value is empty or N/A, ignore it completely
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                # Strip out the ".0" that Pandas adds to numbers
                if val.endswith(".0"):
                    val = val[:-2]
                return val
    return None

def render_student_card(row, cohort, show_subjects=False, show_projected=True, y7_report_type="None"):
    """
    Master rendering function. Adapts to Y7/Y10 and specific report requirements.
    """
    name = row.get("Full Name", "Unknown")
    
    with st.expander(f"👤 {name}"):
        
        # --- 1. HEADER & SUMMARY DASHBOARD ---
        left, right = st.columns([3, 1])
        
        with left:
            st.markdown(f"### {cohort} Profile")
            
            # Smart Summary Generator
            def get_val(keys):
                for k in keys:
                    for row_key in row.keys():
                        if str(row_key).strip().lower() == str(k).strip().lower():
                            val = str(row[row_key]).strip()
                            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL"]:
                                # Strip out the ".0" that Pandas adds to numbers
                                if val.endswith(".0"):
                                    val = val[:-2]
                                # Add a % sign automatically if it's the attendance metric
                                if "attendance" in str(k).lower() and "%" not in val:
                                    val = f"{val}%"
                                return val
                return "" # Returns a perfect blank instead of N/A

            # Added Attendance % and Suspension days
            info = {
                "Form Group": ["Form Tutor", "Tutor", "Form Group"],
                "Gender": ["Gender"],
                "Attendance": ["Attendance %", "Attendance"],
                "Suspensions": ["Suspension days", "Suspensions", "Suspension Days"],
                "SEN Status": ["SEN Status", "SEND Status"],
                "SEN Detail": ["SEN detail", "SEND detail"],
                "Ethnicity": ["Ethnicity"],
                "EAL": ["EAL", "EAL Status"],
                "Disadvantaged": ["Premium", "Disadvantaged", "Pupil Premium", "PP"],
                "KS2 Reading": ["KS2 Read", "KS2 Reading", "SATs Reading"], 
                "KS2 Maths": ["KS2 Maths", "KS2 Math", "SATs Maths"]        
            }

            cols = st.columns(2)
            items = list(info.items())
            for i, (label, keys) in enumerate(items):
                value = get_val(keys)
                cols[i % 2].metric(label, value)
                
        with right:
            display_student_photo(name, cohort)
            
        st.divider()
        
        # 3. Projected Grades (Global)
        if show_projected:
            proj = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
            if proj:
                st.info(f"**Overall Projected Grade:** {proj}")
                
        # --- 4. YEAR 7 CUSTOM REPORTS ---
        if cohort == "Year 7" and y7_report_type != "None":
            st.divider()
            st.markdown(f"### 📑 {y7_report_type} Report")
            
            portrait = get_flexible_text(row, ["Transition Portrait", "Transition portrait", "Portrait"])
            if portrait:
                st.markdown("**Transition Portrait:**")
                st.write(portrait)
                
            home_life = get_flexible_text(row, ["Home Life & Interests", "Home Life", "Home life & interests", "Interests"])
            if home_life:
                st.markdown("**Home Life & Interests:**")
                st.write(home_life)
                
            if y7_report_type == "Detailed":
                st.markdown("**Subject Overviews:**")
                y7_subjects = ["Maths", "English", "Creative Arts", "PE", "Sciences", "Science", "Humanities"]
                
                available_y7 = {}
                for sub in y7_subjects:
                    val = get_flexible_text(row, [sub])
                    if val:
                        available_y7[sub] = val
                
                if available_y7:
                    st.table(available_y7)

        # --- 5. YEAR 10 SUBJECT REPORTS (3-Column Table) ---
        elif show_subjects and cohort == "Year 10":
            st.subheader("Subject Reports")
            subject_cols = [
                "Eng Lang","Eng Lit","Maths","Science","Art","Computing",
                "Design","Drama","Geography","History","Hospitality","Music",
                "Photography","Spanish","Sport"
            ]
            
            table_data = []
            
            # Grab the global predicted grade as a fallback
            global_pred = get_flexible_text(row, ["Projected Grade", "Predicted Grade"]) or ""
            
            for sub in subject_cols:
                grade = get_flexible_text(row, [sub])
                
                if grade: # Only list the subject if they have a current grade for it
                    
                    # SPECIAL RULE FOR SCIENCE (Combining Sci 1 and Sci 2)
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
                            # Fallback if the columns aren't split
                            sub_pred = get_flexible_text(row, ["Science Predicted Grade", "Science Predicted"])
                    
                    # STANDARD RULE FOR ALL OTHER SUBJECTS
                    else:
                        sub_pred = get_flexible_text(row, [f"{sub} Predicted Grade", f"{sub} Predicted", f"Predicted {sub}"])
                    
                    # Use specific prediction, otherwise global prediction, otherwise blank
                    final_pred = sub_pred if sub_pred else global_pred
                    
                    table_data.append({
                        "Subject": sub,
                        "Current Grade": grade,
                        "Predicted Grade": final_pred
                    })
            
            if table_data:
                # Convert the data into a beautiful Pandas DataFrame table
                df_subjects = pd.DataFrame(table_data)
                st.table(df_subjects.set_index("Subject"))


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
