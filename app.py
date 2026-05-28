import streamlit as st
import pandas as pd

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your live, error-free data feed link
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

@st.cache_data(ttl=10) # Checks your Google Sheet for edits every 10 seconds
def load_data():
    return pd.read_csv(DATA_URL)

try:
    df = load_data()
    
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data for teacher training modules. Edits made in your spreadsheet update here instantly.")
    st.write("---")

    # Class Set Filter
    available_sets = sorted(df['Set'].dropna().unique().tolist()) if 'Set' in df.columns else []
    
    if available_sets:
        selected_set = st.selectbox("🎯 Select Academic Set View:", available_sets)
        filtered_df = df[df['Set'] == selected_set]
    else:
        st.warning("Could not find a 'Set' column in your sheet. Verify your column headers match exactly.")
        filtered_df = df

    # Display Class Data Table
    st.subheader(f"Class Roster: {selected_set if available_sets else 'All Students'}")
    st.dataframe(filtered_df, use_container_width=True)
    st.caption(f"Displaying {len(filtered_df)} virtual student profiles in this cohort view.")
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
    st.error("Error connecting to the database. Please verify your link configuration.")
    st.exception(e)
