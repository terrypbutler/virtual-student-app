def render_student_card(row, cohort, show_subjects=False, show_projected=True, y7_report_type="None"):
    """
    Master rendering function. Adapts to Y7/Y9 and specific report requirements.
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
            
            # Both Short and Detailed show these text fields
            portrait = str(row.get("Transition Portrait", "")).strip()
            if portrait and portrait.lower() != "nan":
                st.markdown("**Transition Portrait:**")
                st.write(portrait)
                
            home_life = str(row.get("Home Life & Interests", "")).strip()
            if home_life and home_life.lower() != "nan":
                st.markdown("**Home Life & Interests:**")
                st.write(home_life)
                
            # Only Detailed shows the subjects table
            if y7_report_type == "Detailed":
                st.markdown("**Subject Overviews:**")
                y7_subjects = ["Maths", "English", "Creative Arts", "PE", "Sciences", "Humanities"]
                available_y7 = {
                    sub: row[sub] for sub in y7_subjects 
                    if sub in row.index and str(row[sub]).strip() and str(row[sub]).strip().lower() != "nan"
                }
                
                if available_y7:
                    st.table(available_y7)
                else:
                    st.caption("No subject data available.")

        # --- 5. YEAR 9 SUBJECT REPORTS ---
        elif show_subjects and cohort == "Year 9":
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
