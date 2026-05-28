import streamlit as st
import pandas as pd

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your live Google Sheets CSV data feed link
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

# 🔒 SECURITY CONTROL: Hidden from all dataframes, tables, and reports
COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"] 

@st.cache_data(ttl=10)
def load_data():
    data = pd.read_csv(DATA_URL)
    data.columns = data.columns.str.strip() # Clean hidden spaces from headers
    
    # Drop hidden columns instantly upon loading if they exist
    cols_to_drop = [col for col in COLUMNS_TO_HIDE if col in data.columns]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)
        
    # Replace all blank/empty spreadsheet cells (NaN) with clean spaces
    data = data.fillna("")
    return data

try:
    df = load_data()
    
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data framework for teacher training modules.")
    st.write("---")

    TARGET_COLUMN = "Maths Set"
    NAME_COLUMN = "Full Name"  # ✨ Explicitly targeting your exact column header

    # Class Set Filter Setup
    if TARGET_COLUMN in df.columns:
        available_sets = sorted(df[TARGET_COLUMN].dropna().unique().tolist())
        selected_set = st.selectbox("🎯 Select Academic Set View:", available_sets)
        filtered_df = df[df[TARGET_COLUMN] == selected_set]
        view_label = selected_set
    else:
        st.warning(f"⚠️ Could not find a column named '{TARGET_COLUMN}' in your Google Sheet.")
        filtered_df = df
        view_label = "All Cohorts"

    # Verify Name Column exists to prevent app crashes
    if NAME_COLUMN not in df.columns:
        st.error(f"⚠️ Critical Error: Could not find the '{NAME_COLUMN}' column in your Google Sheet. Please check the spelling.")

    # 🔍 OPTIONAL RAW DATA VIEW
    st.write("")
    if st.checkbox("🔍 View Raw Class Dataset Matrix"):
        st.subheader(f"Raw Data Grid: {view_label}")
        st.dataframe(filtered_df, use_container_width=True)
    st.write("---")

    # Report & Passport Processing Interface
    st.subheader("📋 Report & Passport Generation Panel")
    st.info(f"Select an output template below to process all student records currently loaded for **{view_label}**.")

    # Use a session state flag to remember which button was clicked
    if 'active_report' not in st.session_state:
        st.session_state.active_report = None

    # Draw the 4 buttons side-by-side in narrow columns
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
        st.markdown(f"### 📄 Year 7 Passports — {view_label}")
        cols_to_keep = [col for col in filtered_df.columns if "subject" not in col.lower() and "report" not in col.lower()]
        
        for index, row in filtered_df[cols_to_keep].iterrows
