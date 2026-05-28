import streamlit as st
import pandas as pd

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your live Google Sheets CSV data feed link
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

# 🔒 SECURITY CONTROL: Add the exact names of any columns you want hidden from trainees
COLUMNS_TO_HIDE = ["picture", "Notes", "InternalID", "Admin_Flags"] 

@st.cache_data(ttl=10)
def load_data():
    data = pd.read_csv(DATA_URL)
    data.columns = data.columns.str.strip() # Clean hidden spaces from headers
    
    # Drop hidden columns instantly upon loading if they exist
    cols_to_drop = [col for col in COLUMNS_TO_HIDE if col in data.columns]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)
    return data

try:
    df = load_data()
    
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data framework for teacher training modules.")
    st.write("---")

    TARGET_COLUMN = "Maths Set"

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

    # Display Clean Live Table View
    st.subheader(f"Class Roster Matrix: {view_label}")
    st.dataframe(filtered_df, use_container_width=True)
    st.write("---")

    # Report & Passport Processing Interface
    st.subheader("📋 Report & Passport Generation Panel")
    st.info(f"Select an output template below to process all student records currently loaded for **{view_label}**.")

    col1, col2, col3, col4 = st.columns(4)

    # --- BUTTON 1: YEAR 7 TRANSITION PASSPORT ---
    with col1:
        if st.button("Year 7 Transition Passport", use_container_width=True):
            st.markdown(f"### 📄 Year 7 Passports — {view_label}")
            # Strip out subject reports explicitly
            cols_to_keep = [col for col in filtered_df.columns if "subject" not in col.lower() and "report" not in col.lower()]
            
            for index, row in filtered_df[cols_to_keep].iterrows():
                with st.expander(f"👤 Passport: {row.get('Name', 'Unknown Student')}"):
                    # Professional structural formatting
                    st.markdown(f"#### **Student Profile: {row.get('Name')}**")
                    
                    # Layout key metrics in clean columns inside the card
                    m1, m2 = st.columns(2)
                    if 'Key Stage 2' in row: m1.metric("KS2 Score", row['Key Stage 2'])
                    if 'Reading Age' in row: m2.metric("Reading Age", row['Reading Age'])
                    
                    st.write("---")
                    for col in cols_to_keep:
                        if col not in ['Name', 'Key Stage 2', 'Reading Age']:
                            st.write(f"**{col}:** {row[col]}")

    # --- BUTTON 2: YEAR 7 SUBJECT REPORT ---
    with col2:
        if st.button("Year 7 Subject Report", use_container_width=True):
            st.markdown(f"### 📊 Year 7 Subject Reports — {view_label}")
            
            for index, row in filtered_df.iterrows():
                with st.expander(f"📊 Full Report: {row.get('Name', 'Unknown Student')}"):
                    st.markdown(f"### **Academic Progress Report: {row.get('Name')}**")
                    
                    # Highlight Target vs Current grades if columns exist
                    m1, m2 = st.columns(2)
                    if 'Current Grade' in row: m1.metric("Current Performance", row['Current Grade'])
                    if 'Target Grade' in row: m2.metric("Target Expectation", row['Target Grade'])
                    
                    st.markdown("#### **📚 Subject Performance Breakdown**")
                    subject_data = {}
                    for col in filtered_df.columns:
                        if any(term in col.lower() for term in ["subject", "grade", "score"]):
                            if not any(term in col.lower() for term in ["target", "current", "set", "maths"]):
                                subject_data[col] = [row[col]]
                    
                    if subject_data:
                        # Turn row scores into a sleek, clean summary table
                        summary_table = pd.DataFrame(subject_data).T
                        summary_table.columns = ["Assigned Level / Feedback"]
                        st.table(summary_table)
                    else:
                        st.write("*No supplementary subject columns found.*")

    # --- BUTTON 3: YEAR 9 TRANSITION REPORT ---
    with col3:
        if st.button("Year 9 Transition Report", use_container_width=True):
            st.markdown(f"### 📄 Year 9 Transition Profiles — {view_label}")
            restricted_terms = ["projected", "target", "subject", "report", "grade"]
            cols_to_keep = [col for col in filtered_df.columns if not any(term in col.lower() for term in restricted_terms)]
            
            for index, row in filtered_df[cols_to_keep].iterrows():
                with st.expander(f"📁 Transition Record: {row.get('Name', 'Unknown Student')}"):
                    st.markdown(f"#### **Key Transition Background: {row.get('Name')}**")
                    st.write(f"**Assigned Placement:** Set {row.get(TARGET_COLUMN)}")
                    st.write("---")
                    for col in cols_to_keep:
                        if col not in ['Name', TARGET_COLUMN]:
                            st.write(f"**{col}:** {row[col]}")

    # --- BUTTON 4: YEAR 9 FULL REPORT ---
    with col4:
        if st.button("Year 9 Full Report", use_container_width=True):
            st.markdown(f"### 💯 Full Year 9 Cumulative Reports — {view_label}")
            
            for index, row in filtered_df.iterrows():
                with st.expander(f"🎓 Complete Record: {row.get('Name', 'Unknown Student')}"):
                    st.markdown(f"### **Complete Holistic Overview: {row.get('Name')}**")
                    
                    # Dynamic presentation metrics layout
                    for col in filtered_df.columns:
                        if col != 'Name':
                            st.markdown(f"👉 **{col}:** {row[col]}")

except Exception as e:
    st.error("Error running application layout logic. Verify spreadsheet column titles.")
    st.exception(e)
