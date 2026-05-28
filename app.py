import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your dedicated live Google Sheets CSV data feeds
YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"

COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"] 

@st.cache_data(ttl=10)
def load_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    cols_to_drop = [col for col in COLUMNS_TO_HIDE if col in data.columns]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)
    return data.fillna("")

def display_student_photo(student_name, cohort, is_grid=False):
    safe_name = str(student_name).strip().replace(".", "")
    folder_path = "photos" 
    if not os.path.exists(folder_path):
        st.caption("*(Missing photos folder)*")
        return
    try:
        all_files = os.listdir(folder_path)
        file_map = {f.lower(): f for f in all_files} 
        target_filename = f"{safe_name.lower()}.png"
        
        if target_filename in file_map:
            actual_filename = file_map[target_filename]
            img = Image.open(os.path.join(folder_path, actual_filename))
            width, height = img.size
            
            trim = int(height * 0.08)
            crop_box = (width // 2, trim, width, height - trim) if cohort == "Year 9" else (0, trim, width // 2, height - trim)
            
            # Smaller size for the Grid View (100px), larger for Passport (220px)
            img_width = 100 if is_grid else 220
            st.image(img.crop(crop_box), width=img_width)
        else:
            st.caption(f"*(No photo)*")
    except:
        st.caption("*(Error)*")

try:
    st.title("🎓 Virtual Student Intake Dashboard")
    selected_cohort = st.radio("📅 Select Cohort:", ["Year 7", "Year 9"], horizontal=True)
    df = load_data(YEAR_7_URL if selected_cohort == "Year 7" else YEAR_9_URL)

    NAME_COLUMN = "Full Name" 
    view_type = st.radio("🔍 Group View By:", ["Maths Set", "Tutor Group"], horizontal=True)
    TARGET_COLUMN = "Maths Set" if view_type == "Maths Set" else next((col for col in df.columns if col in ["Form Group", "Tutor Group", "Form Tutor", "Tutor"]), "Form Group")

    available_sets = sorted(df[TARGET_COLUMN].dropna().unique().tolist())
    selected_set = st.selectbox(f"🎯 Select {selected_cohort} {view_type}:", available_sets)
    filtered_df = df[df[TARGET_COLUMN] == selected_set]
    view_label = f"{view_type} {selected_set}"

    if st.button("📋 Generate Reports & Photo Grid"):
        st.session_state.active_report = "active"

    if 'active_report' in st.session_state and st.session_state.active_report == "active":
        # 1. PHOTO GRID
        st.markdown(f"### 🖼️ Photo Grid — {view_label}")
        cols_per_row = 8
        students = filtered_df[NAME_COLUMN].tolist()
        for i in range(0, len(students), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for idx, name in enumerate(students[i : i + cols_per_row]):
                with grid_cols[idx]:
                    display_student_photo(name, selected_cohort, is_grid=True)
                    st.caption(name)

        # 2. DETAILED PASSPORTS
        st.markdown(f"### 📄 Detailed Profiles — {view_label}")
        for index, row in filtered_df.iterrows():
            with st.expander(f"👤 {row[NAME_COLUMN]}"):
                title_col, photo_col = st.columns([3, 1])
                with title_col: st.markdown(f"### **{row[NAME_COLUMN]} ({row.get('DoB', '')})**")
                with photo_col: display_student_photo(row[NAME_COLUMN], selected_cohort)
                
                # HTML Table for demographics
                st.markdown(f"""
                <table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
                    <tr><td><strong>Form Group:</strong> {row.get('Form Group', 'N/A')}</td><td><strong>Gender:</strong> {row.get('Gender', 'N/A')}</td></tr>
                    <tr><td><strong>SEN Status:</strong> {row.get('SEN Status', 'N/A')}</td><td><strong>SEND Detail:</strong> {row.get('SEND detail', 'N/A')}</td></tr>
                    <tr><td><strong>Ethnicity:</strong> {row.get('Ethnicity', 'N/A')}</td><td><strong>EAL Status:</strong> {row.get('EAL', 'N/A')}</td></tr>
                    <tr><td colspan="2"><strong>Disadvantaged (PP):</strong> {row.get('Disadvantaged (PP)', 'N/A')}</td></tr>
                    <tr><td><strong>SATs Reading:</strong> {row.get('SATs Reading', 'N/A')}</td><td><strong>SATs Maths:</strong> {row.get('SATs Maths', 'N/A')}</td></tr>
                </table>
                """, unsafe_allow_html=True)

except Exception as e:
    st.error("Error loading app. Verify column headers match spreadsheet.")
    st.exception(e)
