import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# ✨ NEW: Both of your dedicated live Google Sheets CSV data feeds
YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"

# 🔒 SECURITY CONTROL: Hidden from all dataframes, tables, and reports completely
COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"] 

# The function now takes the URL as an argument so it can switch datasets instantly
@st.cache_data(ttl=10)
def load_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip() # Clean hidden spaces from headers
    
    # Drop hidden columns instantly upon loading if they exist
    cols_to_drop = [col for col in COLUMNS_TO_HIDE if col in data.columns]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)
        
    # Replace all blank/empty spreadsheet cells (NaN) with clean spaces
    data = data.fillna("")
    return data

# Helper function to find, crop, and display the left half of a student photo
def display_student_photo(student_name):
    safe_name = str(student_name).strip().replace(".", "")
    folder_path = "photos" 

    if not os.path.exists(folder_path):
        st.caption("*(Error: 'photos' folder not found)*")
        return

    try:
        all_files = os.listdir(folder_path)
        file_map = {f.lower(): f for f in all_files} 
        
        target_filename = f"{safe_name.lower()}.png"
        
        if target_filename in file_map:
            actual_filename = file_map[target_filename]
            image_path = os.path.join(folder_path, actual_filename)
            try:
                img = Image.open(image_path)
                width, height = img.size
                left_half_box = (0, 0, width // 2, height)
                cropped_img = img.crop(left_half_box)
                st.image(cropped_img, width=150)
            except Exception as e:
                st.caption("*(File is corrupted or not a valid image)*")
        else:
            st.caption(f"*(Missing photo: {safe_name}.png)*")
    except Exception as e:
        st.caption("*(System error scanning files)*")

try:
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data framework for teacher training modules.")
    
    # ✨ NEW: The Cohort Toggle Switch
    selected_cohort = st.radio("📅 Select Cohort:", ["Year 7", "Year 9"], horizontal=True)
    st.write("---")

    # Load the correct URL based on the toggle switch
    if selected_cohort == "Year 7":
        df = load_data(YEAR_7_URL)
    else:
        df = load_data(YEAR_9_URL)

    TARGET_COLUMN = "Maths Set"
    NAME_COLUMN = "Full Name" 
    CUTOFF_COLUMN = "SAT's Maths"  
    DOB_COLUMN = "DoB"  

    # Helper function to generate uniform headers
    def get_header_title(row_data, report_label):
        s_name = str(row_data.get(NAME_COLUMN, "Unknown Student")).strip().upper()
        if DOB_COLUMN in row_data and str(row_data[DOB_COLUMN]).strip():
            s_dob = str(row_data[DOB_COLUMN]).strip()
            return f"{s_name} ({s_dob}) — {report_label}"
        return f"{s_name} — {report_label}"

    def get_val(row_data, keys):
        keys_lower = [k.lower() for k in keys]
        for col in row_data.index:
            if col.lower() in keys_lower and str(row_data[col]).strip() != "":
                return str(row_data[col])
        return "N/A"

    # Class Set Filter Setup (Runs on whichever dataframe is currently loaded)
    if TARGET_COLUMN in df.columns:
        available_sets = sorted(df[TARGET_COLUMN].dropna().unique().tolist())
        selected_set = st.selectbox(f"🎯 Select {selected_cohort} Academic Set:", available_sets)
        filtered_df = df[df[TARGET_COLUMN] == selected_set]
        view_label = selected_set
    else:
        st.warning(f"⚠️ Could not find a column named '{TARGET_COLUMN}' in your Google Sheet.")
        filtered_df = df
        view_label = "All Sets"

    # Verify Crucial Columns exist to prevent app crashes
    if NAME_COLUMN not in df.columns:
        st.error(f"⚠️ Critical Error: Could not find the '{NAME_COLUMN}' column.")
    if DOB_COLUMN not in df.columns:
        st.warning(f"⚠️ Layout Warning: Could not find a column named exact '{DOB_COLUMN}' in your spreadsheet.")

    # 🔍 OPTIONAL RAW DATA VIEW 
    st.write("")
    if st.checkbox(f"🔍 View Raw {selected_cohort} Dataset Matrix"):
        st.subheader(f"Raw Data Grid: {selected_cohort} - Set {view_label}")
        
        if CUTOFF_COLUMN in filtered_df.columns:
            all_cols = list(filtered_df.columns)
            cutoff_index = all_cols.index(CUTOFF_COLUMN)
            allowed_cols = all_cols[:cutoff_index + 1]
            
            if TARGET_COLUMN in allowed_cols:
                allowed_cols.remove(TARGET_COLUMN)
                
            display_df = filtered_df[allowed_cols]
        else:
            st.warning(f"Could not find exact column '{CUTOFF_COLUMN}' to slice layout. Displaying general view.")
            display_df = filtered_df.drop(columns=[TARGET_COLUMN] if TARGET_COLUMN in filtered_df.columns else [])

        st.dataframe(display_df, use_container_width=True)
    st.write("---")

    # Report & Passport Generation Panel
    st.subheader("📋 Report & Passport Generation Panel")
    st.info(f"Select an output template below to process records for **{selected_cohort} - Set {view_label}**.")

    # Use a session state flag to remember which button was clicked
    if 'active_report' not in st.session_state:
        st.session_state.active_report = None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Year 7 Transition Passport", use_container_width=True):
            st.session_state.active_report = "y7_passport"
    with col2:
        if st.button("Year 7 Subject Report", use_container_width=True):
            st.session_state.active_report = "y7_subject"
    with col3:
        if st.button("Year 9 Transition Report", use_container_width=True):
            st.session_state.active_report = "y9_transition"
    with col4:
        if st.button("Year 9 Full Report", use_container_width=True):
            st.session_state.active_report = "y9_full"

    st.write("---")

    # --- FULL WIDTH REPORT RENDERING ---

    # 1. YEAR 7 TRANSITION PASSPORT
    if st.session_state.active_report == "y7_passport":
        st.markdown(f"### 📄 Year 7 Passports — Set {view_label}")
        cols_to_keep = [
            col for col in filtered_df.columns 
            if "subject" not in col.lower() 
            and "report" not in col.lower() 
            and col != TARGET_COLUMN
        ]
        
        for index, row in filtered_df[cols_to_keep].iterrows():
            box_header = get_header_title(row, "Year 7 Passport")
            s_name = str(row.get(NAME_COLUMN, "Unknown Student"))
            s_dob = str(row.get(DOB_COLUMN, "")).strip()
            
            with st.expander(f"👤 {box_header}"):
                
                title_col, photo_col = st.columns([3, 1])
                
                with title_col:
                    if s_dob:
                        st.markdown(f"### **{s_name} ({s_dob})**")
                    else:
                        st.markdown(f"### **{s_name}**")
                        
                with photo_col:
                    display_student_photo(s_name)
                
                form_keys = ["Form Tutor", "Tutor", "Form Group"]
                gender_keys = ["Gender"]
                sen_status_keys = ["SEN Status", "SEND Status"]
                sen_detail_keys = ["SEND detail", "SEN detail"]
                eth_keys = ["Ethnicity"]
                eal_keys = ["EAL", "EAL Status"]
                dis_keys = ["Premium", "Disadvantaged", "Pupil Premium", "Disadvantaged (PP)"]
                read_keys = ["SATs Reading", "SAT's Reading", "Reading Score"]
                math_keys = ["SATs Maths", "SAT's Maths", "Maths Score"]
                
                form_val = get_val(row, form_keys)
                gender_val = get_val(row, gender_keys)
                sen_status_val = get_val(row, sen_status_keys)
                sen_detail_val = get_val(row, sen_detail_keys)
                eth_val = get_val(row, eth_keys)
                eal_val = get_val(row, eal_keys)
                dis_val = get_val(row, dis_keys)
                read_val = get_val(row, read_keys)
                math_val = get_val(row, math_keys)

                table_html = f"""
                <table style="width:100%; text-align:left; border: 1px solid #ddd; border-collapse: collapse; margin-bottom: 15px; background-color: white;">
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px; width: 50%;"><strong>Form Group:</strong> {form_val}</td>
                        <td style="border: 1px solid #ddd; padding: 10px; width: 50%;"><strong>Gender:</strong> {gender_val}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SEN Status:</strong> {sen_status_val}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SEND Detail:</strong> {sen_detail_val}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>Ethnicity:</strong> {eth_val}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>EAL Status:</strong> {eal_val}</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="border: 1px solid #ddd; padding: 10px;"><strong>Disadvantaged (PP):</strong> {dis_val}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SATs Reading:</strong> {read_val}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SATs Maths:</strong> {math_val}</td>
                    </tr>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                    
                handled_keys = form_keys + gender_keys + sen_status_keys + sen_detail_keys + eth_keys + eal_keys + dis_keys + read_keys + math_keys
                handled_cols_lower = [NAME_COLUMN.lower(), DOB_COLUMN.lower()] + [k.lower() for k in handled_keys]
                
                leftover_cols = [c for c in cols_to_keep if c.lower() not in handled_cols_lower]
                
                if leftover_cols:
                    left_col, right_col = st.columns(2)
                    for i, col in enumerate(leftover_cols):
                        if i % 2 == 0:
                            left_col.markdown(f"**{col}:** {row[col]}")
                        else:
                            right_col.markdown(f"**{col}:** {row[col]}")

    # 2. YEAR 7 SUBJECT REPORT
    elif st.session_state.active_report == "y7_subject":
        st.markdown(f"### 📊 Year 7 Subject Reports — Set {view_label}")
        
        for index, row in filtered_df.iterrows():
            box_header = get_header_title(row, "Academic Progress Report")
            s_name = str(row.get(NAME_COLUMN, "Unknown Student"))
            s_dob = str(row.get(DOB_COLUMN, "")).strip()
            
            with st.expander(f"📊 {box_header}"):
                
                title_col, photo_col = st.columns([3, 1])
                with title_col:
                    if s_dob:
                        st.markdown(f"### **Academic Progress Report: {s_name} ({s_dob})**")
                    else:
                        st.markdown(f"### **Academic Progress Report: {s_name}**")
                        
                with photo_col:
                    display_student_photo(s_name)
                
                m1, m2 = st.columns(2)
                m1.metric("Current Working Grade", row.get('Current Grade', 'N/A'))
                m2.metric("Target Minimum Expectation", row.get('Target Grade', 'N/A'))
                st.write("---")
                
                form_keys = ["Form Tutor", "Tutor", "Form Group"]
                gender_keys = ["Gender"]
                sen_status_keys = ["SEN Status", "SEND Status"]
                sen_detail_keys = ["SEND detail", "SEN detail"]
                eth_keys = ["Ethnicity"]
                eal_keys = ["EAL", "EAL Status"]
                dis_keys = ["Premium", "Disadvantaged", "Pupil Premium", "Disadvantaged (PP)"]
                read_keys = ["SATs Reading", "SAT's Reading", "Reading Score"]
                math_keys = ["SATs Maths", "SAT's Maths", "Maths Score"]
                
                form_val = get_val(row, form_keys)
                gender_val = get_val(row, gender_keys)
                sen_status_val = get_val(row, sen_status_keys)
                sen_detail_val = get_val(row, sen_detail_keys)
                eth_val = get_val(row, eth_keys)
                eal_val = get_val(row, eal_keys)
                dis_val = get_val(row, dis_keys)
                read_val = get_val(row, read_keys)
                math_val = get_val(row, math_keys)

                table_html = f"""
                <table style="width:100%; text-align:left; border: 1px solid #ddd; border-collapse: collapse; margin-bottom: 15px; background-color: white;">
