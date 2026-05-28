import streamlit as st
import pandas as pd

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# Your live Google Sheets CSV data feed link
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"

# 🔒 SECURITY CONTROL: Hidden from all dataframes, tables, and reports completely
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
    NAME_COLUMN = "Full Name" 
    CUTOFF_COLUMN = "SAT's Maths"  
    DOB_COLUMN = "DoB"  # Locked onto your exact header: DoB

    # Helper function to generate uniform headers with Name and DOB side-by-side
    def get_header_title(row_data, report_label):
        s_name = str(row_data.get(NAME_COLUMN, "Unknown Student")).strip().upper()
        if DOB_COLUMN in row_data and str(row_data[DOB_COLUMN]).strip():
            s_dob = str(row_data[DOB_COLUMN]).strip()
            return f"{s_name} ({s_dob}) — {report_label}"
        return f"{s_name} — {report_label}"

    # Helper function to safely grab data for the strict HTML table mapping
    def get_val(row_data, keys):
        for k in keys:
            if k in row_data.index and str(row_data[k]).strip() != "":
                return str(row_data[k])
        return "N/A"

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

    # Verify Crucial Columns exist to prevent app crashes
    if NAME_COLUMN not in df.columns:
        st.error(f"⚠️ Critical Error: Could not find the '{NAME_COLUMN}' column.")
    if DOB_COLUMN not in df.columns:
        st.warning(f"⚠️ Layout Warning: Could not find a column named exact '{DOB_COLUMN}' in your spreadsheet.")

    # 🔍 OPTIONAL RAW DATA VIEW 
    st.write("")
    if st.checkbox("🔍 View Raw Class Dataset Matrix"):
        st.subheader(f"Raw Data Grid: {view_label}")
        
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
                # Top Headers stay exactly where they are
                if s_dob:
                    st.markdown(f"### **{s_name} ({s_dob})**")
                else:
                    st.markdown(f"### **{s_name}**")
                
                # ✨ NEW HTML MULTI-CELL TABLE
                form_val = get_val(row, ["Form Tutor", "Tutor", "Form Group"])
                gender_val = get_val(row, ["Gender"])
                sen_status_val = get_val(row, ["SEN Status", "SEND Status"])
                sen_detail_val = get_val(row, ["SEND detail", "SEN detail"])
                eth_val = get_val(row, ["Ethnicity"])
                eal_val = get_val(row, ["EAL", "EAL Status"])
                dis_val = get_val(row, ["Premium", "Disadvantaged", "Pupil Premium"])
                read_val = get_val(row, ["SAT's Reading", "Reading Score", "Reading Age"])
                math_val = get_val(row, ["SAT's Maths", "Maths Score"])

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
                        <td colspan="2" style="border: 1px solid #ddd; padding: 10px;"><strong>Disadvantaged:</strong> {dis_val}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SAT's Reading:</strong> {read_val}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SAT's Maths:</strong> {math_val}</td>
                    </tr>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                    
                # Loop out any trailing miscellaneous notes columns left over in the background
                handled_keys = ["Form Tutor", "Tutor", "Form Group", "Gender", "SEN Status", "SEND Status", "SEND detail", "SEN detail", "Ethnicity", "EAL", "EAL Status", "Premium", "Disadvantaged", "Pupil Premium", "SAT's Reading", "Reading Score", "Reading Age", "SAT's Maths", "Maths Score"]
                handled_cols = [NAME_COLUMN, DOB_COLUMN] + handled_keys
                leftover_cols = [c for c in cols_to_keep if c not in handled_cols]
                
                if leftover_cols:
                    left_col, right_col = st.columns(2)
                    for i, col in enumerate(leftover_cols):
                        if i % 2 == 0:
                            left_col.markdown(f"**{col}:** {row[col]}")
                        else:
                            right_col.markdown(f"**{col}:** {row[col]}")

    # 2. YEAR 7 SUBJECT REPORT
    elif st.session_state.active_report == "y7_subject":
        st.markdown(f"### 📊 Year 7 Subject Reports — {view_label}")
        
        for index, row in filtered_df.iterrows():
            box_header = get_header_title(row, "Academic Progress Report")
            s_name = str(row.get(NAME_COLUMN, "Unknown Student"))
            s_dob = str(row.get(DOB_COLUMN, "")).strip()
            
            with st.expander(f"📊 {box_header}"):
                if s_dob:
                    st.markdown(f"### **Academic Progress Report: {s_name} ({s_dob})**")
                else:
                    st.markdown(f"### **Academic Progress Report: {s_name}**")
                
                # Current/Target Metrics
                m1, m2 = st.columns(2)
                m1.metric("Current Working Grade", row.get('Current Grade', 'N/A'))
                m2.metric("Target Minimum Expectation", row.get('Target Grade', 'N/A'))
                st.write("---")
                
                # ✨ NEW HTML MULTI-CELL TABLE (Mirrors Passport Profile exactly)
                form_val = get_val(row, ["Form Tutor", "Tutor", "Form Group"])
                gender_val = get_val(row, ["Gender"])
                sen_status_val = get_val(row, ["SEN Status", "SEND Status"])
                sen_detail_val = get_val(row, ["SEND detail", "SEN detail"])
                eth_val = get_val(row, ["Ethnicity"])
                eal_val = get_val(row, ["EAL", "EAL Status"])
                dis_val = get_val(row, ["Premium", "Disadvantaged", "Pupil Premium"])
                read_val = get_val(row, ["SAT's Reading", "Reading Score", "Reading Age"])
                math_val = get_val(row, ["SAT's Maths", "Maths Score"])

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
                        <td colspan="2" style="border: 1px solid #ddd; padding: 10px;"><strong>Disadvantaged:</strong> {dis_val}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SAT's Reading:</strong> {read_val}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;"><strong>SAT's Maths:</strong> {math_val}</td>
                    </tr>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
                st.write("---")
                st.markdown("#### **📚 Subject Performance Breakdown**")
                
                subject_data = {}
                for col in filtered_df.columns:
                    if any(term in col.lower() for term in ["subject", "grade", "score"]):
                        if not any(term in col.lower() for term in ["target", "current", "set", "maths", "cutoff"]):
                            subject_data[col] = [row[col]]
                
                if subject_data:
                    summary_table = pd.DataFrame(subject_data).T
                    summary_table.columns = ["Assigned Level / Progress Tracker"]
                    st.dataframe(summary_table, use_container_width=True)
                else:
                    st.caption("*No supplementary internal school subject columns found in database.*")

    # 3. YEAR 9 TRANSITION REPORT
    elif st.session_state.active_report == "y9_transition":
        st.markdown(f"### 📄 Year 9 Transition Profiles — {view_label}")
        restricted_terms = ["projected", "target", "subject", "report", "grade"]
        cols_to_keep = [
            col for col in filtered_df.columns 
            if not any(term in col.lower() for term in restricted_terms)
            and col != TARGET_COLUMN
        ]
        
        for index, row in filtered_df[cols_to_keep].iterrows():
            box_header = get_header_title(row, "Year 9 Transition Profile")
            with st.expander(f"📁 {box_header}"):
                st.markdown(f"### **Key Transition Profile: {row.get(NAME_COLUMN)}**")
                st.write("---")
                
                info_col1, info_col2 = st.columns(2)
                display_cols = [col for col in cols_to_keep if col not in [NAME_COLUMN, DOB_COLUMN]]
                for i, col in enumerate(display_cols):
                    if i % 2 == 0:
                        info_col1.markdown(f"🔹 **{col}:** {row[col]}")
                    else:
                        info_col2.markdown(f"🔹 **{col}:** {row[col]}")

    # 4. YEAR 9 FULL REPORT
    elif st.session_state.active_report == "y9_full":
        st.markdown(f"### 💯 Full Year 9 Cumulative Reports — {view_label}")
        
        for index, row in filtered_df.iterrows():
            box_header = get_header_title(row, "Full Holistic Record")
            with st.expander(f"🎓 {box_header}"):
                st.write("---")
                
                c1, c2, c3 = st.columns(3)
                all_cols = [col for col in filtered_df.columns if col not in [NAME_COLUMN, DOB_COLUMN]]
                
                for i, col in enumerate(all_cols):
                    content_string = f"📌 **{col}:** {row[col]}"
                    if i % 3 == 0:
                        c1.markdown(content_string)
                    elif i % 3 == 1:
                        c2.markdown(content_string)
                    else:
                        c3.markdown(content_string)

except Exception as e:
    st.error("Error running application layout logic. Verify spreadsheet column titles.")
    st.exception(e)
