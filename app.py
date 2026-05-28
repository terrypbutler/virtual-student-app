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

    # Clean up column names (removes hidden leading/trailing spaces)
    df.columns = df.columns.str.strip()

    # Configure the filtering column to match your spreadsheet exactly
    TARGET_COLUMN = "Maths Set"

    # 1. Class Set Filter Setup
    if TARGET_COLUMN in df.columns:
        available_sets = sorted(df[TARGET_COLUMN].dropna().unique().tolist())
        selected_set = st.selectbox("🎯 Select Academic Set View:", available_sets)
        filtered_df = df[df[TARGET_COLUMN] == selected_set]
        view_label = selected_set
    else:
        # Fallback security if the column header is ever renamed
        st.warning(f"⚠️ Could not find a column named '{TARGET_COLUMN}' in your Google Sheet.")
        with st.expander("🔍 Click to see the actual column names found in your sheet:"):
            st.write(list(df.columns))
        
        filtered_df = df
        view_label = "All Cohorts"

    # Display Live Table View
    st.subheader(f"Class Roster Matrix: {view_label}")
    st.dataframe(filtered_df, use_container_width=True)
    st.write("---")

    # 2. Report & Passport Processing Interface
    st.subheader("📋 Report & Passport Generation Panel")
    st.info(f"Select an output template below to process all student records currently loaded for **{view_label}**.")

    col1, col2, col3, col4 = st.columns(4)

    # --- BUTTON 1: YEAR 7 TRANSITION PASSPORT ---
    with col1:
        if st.button("Year 7 Transition Passport", use_container_width=True):
            st.subheader(f"📄 Generated Year 7 Passports — {view_label}")
            cols_to_keep = [col for col in filtered_df.columns if "subject" not in col.lower() and "report" not in col.lower()]
            passport_df = filtered_df[cols_to_keep]
            
            for index, row in passport_df.iterrows():
                with st.expander(f"Passport: {row.get('Name', 'Unknown Student')}"):
                    for col in cols_to_keep:
                        if col != 'Name':
                            st.write(f"**{col}:** {row[col]}")

    # --- BUTTON 2: YEAR 7 SUBJECT REPORT ---
    with col2:
        if st.button("Year 7 Subject Report", use_container_width=True):
            st.subheader(f"📊 Generated Year 7 Subject Reports — {view_label}")
            
            for index, row in filtered_df.iterrows():
                with st.expander(f"Full Report: {row.get('Name', 'Unknown Student')}"):
                    st.markdown("### 📚 Subject Performance Breakdowns")
                    subject_data = {}
                    for col in filtered_df.columns:
                        if any(term in col.lower() for term in ["subject", "grade", "score"]):
                            if not any(term in col.lower() for term in ["target", "current", "set"]):
                                subject_data[col] = [row[col]]
                    
                    if subject_data:
                        st.table(pd.DataFrame(subject_data))
                    else:
                        st.write("*No subject-specific columns found in spreadsheet.*")

    # --- BUTTON 3: YEAR 9 TRANSITION REPORT ---
    with col3:
        if st.button("Year 9 Transition Report", use_container_width=True):
            st.subheader(f"📄 Generated Year 9 Transition Profiles — {view_label}")
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
        if st.button("Year 9 Full Report", use_container_width=True):
            st.subheader(f"💯 Generated Full Year 9 Reports — {view_label}")
            
            for index, row in filtered_df.iterrows():
                with st.expander(f"Complete Cohort Record: {row.get('Name', 'Unknown Student')}"):
                    for col in filtered_df.columns:
                        if col != 'Name':
                            st.write(f"**{col}:** {row[col]}")

except Exception as e:
    st.error("Error running application logic. Please check your data or script layout.")
    st.exception(e)
    
