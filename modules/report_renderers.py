import streamlit as st
from modules.ui_components import render_student_header, render_student_summary
from modules.photo_utils import display_student_photo

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

# --- NEW FUNCTION FOR THE GRID ---
def render_photo_grid(df, cohort, num_cols=5):
    """
    Renders a grid of student photos based on the filtered dataframe.
    """
    if df.empty:
        st.warning("No students found for this selection.")
        return

    # Create the columns for the grid
    cols = st.columns(num_cols)
    
    # Loop through the filtered students and distribute them across the columns
    for index, (_, row) in enumerate(df.iterrows()):
        name = row.get("Full Name", "Unknown")
        
        # This math ensures photos wrap around to the next row automatically
        col = cols[index % num_cols]
        
        with col:
            display_student_photo(name, cohort)
            # Add the name underneath the photo, centered
            st.markdown(f"<p style='text-align: center; font-weight: bold;'>{name}</p>", unsafe_allow_html=True)
            st.write("---") # Visual separator between rows
