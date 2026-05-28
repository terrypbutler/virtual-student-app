import streamlit as st
import pandas as pd

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your live Google Sheets CSV data feed link
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_csv(DATA_URL)

try:
    df = load_data()
    
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data for teacher training modules.")
    st.write("---")

    # 1. Class Set Filter Setup
    available_sets = sorted(df['Set'].dropna().unique().tolist()) if 'Set' in df.columns else []
    
    if available_sets:
        selected_set = st.selectbox("🎯 Select Academic Set View:", available_sets)
        filtered_df = df[df['Set'] == selected_set]
    else:
        st.warning("Could not find a 'Set' column in your sheet.")
        filtered_df = df

    # Display Live Table View
    st.subheader(f"Class Roster Matrix: {selected_set if available_sets else 'All Students'}")
    st.dataframe(filtered_df, use_container_width=True)
    st.write("---")

    # 2. Report & Passport Processing Interface
    st.subheader("📋 Report & Passport Generation Panel")
    st.info(f"Select an output template below to process all student records currently loaded for **{selected_set}**.")

    col1, col2, col3, col4 = st.columns(4)

    # --- BUTTON 1: YEAR 7 TRANSITION PASSPORT ---
    with col1:
        if st.button("Year 7 Transition Passport", use_container_width=True, help="Year 7 data without subject reports"):
            st.subheader(f"📄 Generated Year 7 Passports — {selected_set}")
            # Filter out subject reports completely if columns exist
            cols_to_keep = [col for col in filtered_df.columns if "Subject" not in col and "Report" not in col]
            passport_df = filtered_df[cols_to_keep]
            
            for index, row in passport_df.iterrows():
                with st.expander(f"Passport: {row.get('Name', 'Unknown Student')}"):
                    st.write(f"**Academic Set Assignment:** {row.get('Set', 'N/A')}")
                    # Dynamically list all other non-subject data metrics
                    for col in cols_to_keep:
                        if col not in ['Name', 'Set']:
                            st.write(f"**{col}:** {row[col]}")

    # --- BUTTON 2: YEAR 7 SUBJECT REPORT ---
    with col2:
        if st.button("Year 7 Subject Report", use_container_width=True, help="Year 7 data with a table showing subject reports"):
            st.subheader(f"📊 Generated Year 7 Subject Reports — {selected_set}")
            
            for index, row in filtered_df.iterrows():
                with st.expander(f"Full Report: {row.get('Name', 'Unknown Student')}"):
                    st.markdown("### 🔑 Core Demographics & Metrics")
                    st.write(f"**Current Set:** {row.get('Set', 'N/A')}")
                    
                    # Separate data into a visual "Subject Scores" block
                    st.markdown("### 📚 Subject Performance Breakdowns")
                    subject_data = {}
                    for col in filtered_df.columns:
                        if "Subject" in col or "Grade" in col or "Score" in col:
                            if col not in ['Target Grade', 'Current Grade', 'Set']:
                                subject_data[col] = [row[col]]
                    
                    if subject_data:
                        st.table(pd.DataFrame(subject_data))
                    else:
                        st.write("*No subject-specific columns found in spreadsheet.*")

    # --- BUTTON 3: YEAR 9 TRANSITION REPORT ---
    with col3:
        if st.button("Year 9 Transition Report", use_container_width=True, help="All data except projected grades/subject reports"):
            st.subheader(f"📄 Generated Year 9 Transition Profiles — {selected_set}")
            # Strip out projected grades and subject reports
            restricted_terms = ["projected", "target", "subject", "report", "grade"]
            cols_to_keep = [col for col in filtered_df.columns if not any(term in col.lower() for term in restricted_terms)]
            transition_df = filtered_df[cols_to_keep]
            
            for index, row in transition_df.iterrows():
                with st.expander(f"Transition Record: {row.get('Name', 'Unknown Student')}"):
                    for col in cols_to_keep:
                        if col != 'Name':
                            st.write(f"**{col}:** {row[col]}")

    # --- BUTTON 4: YEAR 9 FULL REPORT ---
    with col4:
        if st.button("Year 9 Full Report", use_container_width=True, help="All data metrics fully populated"):
            st.subheader(f"💯 Generated Full Year 9 Reports — {selected_set}")
            
            for index, row in filtered_df.iterrows():
                with st.expander(f"Complete Cohort Record: {row.get('Name', 'Unknown Student')}"):
                    # Loop through absolutely every single column inside the spreadsheet row
                    for col in filtered_df.columns:
                        if col != 'Name':
                            st.write(f"**{col}:** {row[col]}")

except Exception as e:
    st.error("Error running application logic. Please check your data or script layout.")
    st.exception(e)
