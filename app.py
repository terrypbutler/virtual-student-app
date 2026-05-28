import streamlit as st
import pandas as pd

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your personal OneDrive link converted to a direct data stream
EXCEL_LIVE_URL = "https://1drv.ms/x/c/4e58796b40951c18/IQQQ019JbjbJTpN5nkOfl2hZATe8W6mRfUzc1KldB8qTCRw?download=1"

@st.cache_data(ttl=10) # Refreshes very quickly (every 10 seconds) for easy testing
def load_data():
    # Reads the live OneDrive Excel file directly into Python
    return pd.read_excel(EXCEL_LIVE_URL)

try:
    df = load_data()
    
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data pulling securely from OneDrive. Edits made in Excel update here.")
    st.write("---")

    # Class Set Filter
    available_sets = sorted(df['Set'].unique().tolist()) if 'Set' in df.columns else []
    
    if available_sets:
        selected_set = st.selectbox("🎯 Select Academic Set View:", available_sets)
        filtered_df = df[df['Set'] == selected_set]
    else:
        st.warning("Could not find a 'Set' column in your Excel sheet. Make sure you have a column named exactly 'Set' (case-sensitive).")
        filtered_df = df

    # Display Class Data Table
    st.subheader(f"Class Roster: {selected_set if available_sets else 'All Students'}")
    st.dataframe(filtered_df, use_container_width=True)
    st.caption(f"Displaying {len(filtered_df)} virtual student profiles.")
    st.write("---")

    # The 4 Action Buttons
    st.subheader("📋 Report & Passport Generation")
    st.info("Click a button below to process data specifically for the selected set.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Year 7 Transition Passport", use_container_width=True):
            st.success("Passports generated (Year 7 data, no subject reports).")

    with col2:
        if st.button("Year 7 Subject Report", use_container_width=True):
            st.success("Subject Reports generated (Year 7 data + subjects table).")

    with col3:
        if st.button("Year 9 Transition Report", use_container_width=True):
            st.success("Transition Reports generated (All data, no projected grades/subject reports).")

    with col4:
        if st.button("Year 9 Full Report", use_container_width=True):
            st.success("Full Year 9 Reports generated (All data fully populated).")

except Exception as e:
    st.error("Error connecting to your Excel database. Please check your URL configuration.")
    st.exception(e)
