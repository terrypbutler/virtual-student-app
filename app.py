import streamlit as st
import pandas as pd
import altair as alt
from modules.data_loader import load_data
from modules.report_renderers import render_student_card, render_photo_grid

def safe_unique(df, col):
    if col in df.columns:
        return sorted(df[col].dropna().astype(str).unique().tolist())
    return []

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Butler Academy MIS", layout="wide")

YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"
YEAR_10_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"

# ---------------------------
# DATA LOAD
# ---------------------------
df_y7 = load_data(YEAR_7_URL)
df_y10 = load_data(YEAR_10_URL)

# ---------------------------
# SIDEBAR NAV
# ---------------------------
st.sidebar.title("🎓 Butler Academy")

page = st.sidebar.radio(
    "Navigate",
    [
        "Student Search",
        "Year 7",
        "Year 10",
        "Analytics"
    ],
    key="sidebar_nav"
)

# ---------------------------
# CSS PRINT INJECTION
# ---------------------------
def inject_print_css():
    st.markdown("""
        <style>
        @media print {
            /* Hide the sidebar and top navigation bars */
            section[data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            
            /* Remove margins so content stretches */
            .stApp { margin-top: -50px !important; }
            
            /* Hide the expander toggle arrows */
            svg[data-testid="stExpanderToggleIcon"] { display: none !important; }
        }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------
# SEARCH PAGE
# ---------------------------
def student_search(df_y7, df_y10):
    st.title("🔍 Student Search (MIS View)")
    
    search_cohort = st.radio("Select Cohort to Search:", ["Year 7", "Year 10"], horizontal=True)
    
    df = df_y7 if search_cohort == "Year 7" else df_y10

    query = st.text_input("Search student name", key="search_name")

    if query:
        results = df[df["Full Name"].str.contains(query, case=False, na=False)]
        st.write(f"Found {len(results)} students")

        if len(results) == 0:
            st.warning("No matches found.")

        for _, row in results.iterrows():
            render_student_card(row, search_cohort, show_projected=True, report_type="Detailed")

# ---------------------------
# ANALYTICS
# ---------------------------
def analytics(df_y7, df_y10):
    st.title("📊 Cohort Analytics Dashboard")

    analytics_cohort = st.radio("Select Cohort to Analyze:", ["Year 7", "Year 10"], horizontal=True)
    df_base = df_y7 if analytics_cohort == "Year 7" else df_y10

    st.sidebar.subheader("🔎 Analytics Filters")

    form_groups = safe_unique(df_base, "Form Group")
    maths_sets = safe_unique(df_base, "Maths Set")

    selected_form = st.sidebar.multiselect("Form Tutor Group", form_groups, key="ana_form")
    selected_math = st.sidebar.multiselect("Maths Set", maths_sets, key="ana_math")

    subject_cols = [
        "Eng Lang","Eng Lit","Maths","Science","Art","Computing","Design",
        "Drama","Geography","History","Hospitality","Music","Photography",
        "Spanish","Sport"
    ]
    available_subjects = [c for c in subject_cols if c in df_base.columns]
    selected_subject = st.sidebar.selectbox("Option Class (optional)", ["All Subjects"] + available_subjects, key="ana_sub")

    df = df_base.copy()
    if selected_form:
        df = df[df["Form Group"].astype(str).isin(selected_form)]
    if selected_math:
        df = df[df["Maths Set"].astype(str).isin(selected_math)]
    if selected_subject != "All Subjects":
        df = df[
            df[selected_subject].notna() &
            (df[selected_subject].astype(str).str.strip() != "")
        ]

    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN", "0", "0.0"]
    
    def count_active(col_names):
        col = next((c for c in df.columns if c.strip().lower() in [n.lower() for n in col_names]), None)
        if col:
            return df[col].astype(str).str.upper().apply(lambda x: x.strip() not in ignore_list).sum()
        return 0

    sen_count = count_active(["SEN Status", "SEND Status"])
    eal_count = count_active(["EAL", "EAL Status"])
    pp_count = count_active([
        "Disadvantaged (PP)", "Premium", "Disadvantaged", "Pupil Premium", "PP", 
        "FSM", "Ever 6", "FSM6", "Pupil Premium Indicator"
    ])

    st.subheader(f"Overview: {len(df)} Students")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", len(df))
    m2.metric("SEN Support", sen_count)
    m3.metric("EAL", eal_count)
    m4.metric("Pupil Premium", pp_count)

    st.write("---")

    st.subheader("📈 KS2 / SATs Performance")
    g1, g2 = st.columns(2)
    
    read_col = next((c for c in df.columns if c.strip().lower() in ["ks2 read", "ks2 reading", "sats reading", "reading score"]), None)
    math_col = next((c for c in df.columns if c.strip().lower() in ["ks2 maths", "ks2 math", "sats maths", "maths score"]), None)
    
    ks2_bins = [80, 85, 90, 95, 100, 105, 110, 115, 121] 
    ks2_labels = ["80-84", "85-89", "90-94", "95-99", "100-104", "105-109", "110-114", "115-120"]
    
    with g1:
        if math_col:
            st.markdown("**Maths Distribution**")
            math_nums = pd.to_numeric(df[math_col], errors='coerce').dropna()
            math_binned = pd.cut(math_nums, bins=ks2_bins, labels=ks2_labels, right=False)
            math_counts = math_binned.value_counts().reindex(ks2_labels, fill_value=0)
            
            df_math = pd.DataFrame({"Score Range": ks2_labels, "Students": math_counts.values})
            
            chart_math = alt.Chart(df_math).mark_bar().encode(
                x=alt.X('Score Range', sort=ks2_labels, title="Score Range"),
                y=alt.Y('Students', scale=alt.Scale(domain=[0, 15]), title="Students")
            )
            st.altair_chart(chart_math, use_container_width=True)
        else:
            st.caption("*(No Maths data available)*")
            
    with g2:
        if read_col:
            st.markdown("**Reading Distribution**")
            read_nums = pd.to_numeric(df[read_col], errors='coerce').dropna()
            read_binned = pd.cut(read_nums, bins=ks2_bins, labels=ks2_labels, right=False)
            read_counts = read_binned.value_counts().reindex(ks2_labels, fill_value=0)
            
            df_read = pd.DataFrame({"Score Range": ks2_labels, "Students": read_counts.values})
            
            chart_read = alt.Chart(df_read).mark_bar().encode(
                x=alt.X('Score Range', sort=ks2_labels, title="Score Range"),
                y=alt.Y('Students', scale=alt.Scale(domain=[0, 15]), title="Students")
            )
            st.altair_chart(chart_read, use_container_width=True)
        else:
            st.caption("*(No Reading data available)*")

    st.write("---")
    
    st.subheader("Raw Data")
    if analytics_cohort == "Year 7":
        desired_cols = [
            "Full Name", "Form Group", "Maths Set", "DoB", "Gender", 
            "SEN Status", "Disadvantaged (PP)", "Ethnicity", "EAL Status", 
            "SATs Reading", "SAT's Maths"
        ]
    else:
        desired_cols = [
            "Full Name", "Form Group", "Maths Set", "DoB", "Gender", 
            "SEN Status", "SEND Detail", "Disadvantaged (PP)", "Ethnicity", 
            "KS2 Read", "KS2 Maths", "EAL Status", "Eng Lang Predicted Grade", 
            "Eng Lit Predicted Grade", "Maths Predicted Grade", "Sci 1 Predicted Grade", 
            "Sci 2 Predicted Grade", "Art Predicted Grade", "Computing Predicted Grade", 
            "Design Predicted Grade", "Drama Predicted Grade", "Geography Predicted Grade", 
            "History Predicted Grade", "Hospitality Predicted Grade", "Music Predicted Grade", 
            "Photography Predicted Grade", "Spanish Predicted Grade", "Sport Predicted Grade", 
            "Attendance %", "Suspension days"
        ]
        
    final_cols = [col for col in desired_cols if col in df.columns]
    st.dataframe(df[final_cols], use_container_width=True)

# ---------------------------
# ROUTING & FILTERS
# ---------------------------
if page == "Student Search":
    student_search(df_y7, df_y10)

# ------------------ YEAR 7 ------------------
elif page == "Year 7":
    df = df_y7 
    
    st.sidebar.subheader("🔎 Filters (Year 7)")

    form_groups = safe_unique(df, "Form Group")
    maths_sets = safe_unique(df, "Maths Set")

    selected_form = st.sidebar.multiselect("Form Group (ALL by default)", form_groups, key="y7_form")
    selected_math = st.sidebar.multiselect("Maths Set (ALL by default)", maths_sets, key="y7_math")

    filtered_df = df.copy()

    if selected_form:
        filtered_df = filtered_df[filtered_df["Form Group"].astype(str).isin(selected_form)]
    if selected_math:
        filtered_df = filtered_df[filtered_df["Maths Set"].astype(str).isin(selected_math)]

    st.sidebar.divider()
    report_option = st.sidebar.radio(
        "Select Report Detail",
        ["Base Passport (No Details)", "Short Report (Portrait & Home Life)", "Detailed Report (All Subjects)"]
    )
    
    # --- PRINT MODE TOGGLE ---
    st.sidebar.divider()
    print_mode = st.sidebar.toggle("🖨️ Enable Print View", value=False)
    
    if print_mode:
        inject_print_css()
        st.success("🖨️ **Print View Ready!** Press `Ctrl + P` (Windows) or `Cmd + P` (Mac) and select **Save as PDF** to generate your document.")

    mode = "None"
    if report_option == "Short Report (Portrait & Home Life)":
        mode = "Short"
    elif report_option == "Detailed Report (All Subjects)":
        mode = "Detailed"

    st.subheader(f"Showing {len(filtered_df)} Students")
    
    render_photo_grid(filtered_df, "Year 7", num_cols=5)
    
    st.divider()
    st.subheader("📄 Detailed Passports")
    
    for _, row in filtered_df.iterrows():
        # Pass the print_mode setting to the cards
        render_student_card(row, "Year 7", show_projected=True, report_type=mode, is_print_mode=print_mode)

# ------------------ YEAR 10 ------------------
elif page == "Year 10":
    df = df_y10 
    
    st.sidebar.subheader("🔎 Filters (Year 10)")

    form_groups = safe_unique(df, "Form Group")
    maths_sets = safe_unique(df, "Maths Set")

    selected_form = st.sidebar.multiselect("Form Group (ALL by default)", form_groups, key="y10_form")
    selected_math = st.sidebar.multiselect("Maths Set (ALL by default)", maths_sets, key="y10_math")

    subject_cols = [
        "Eng Lang","Eng Lit","Maths","Science","Art","Computing","Design",
        "Drama","Geography","History","Hospitality","Music","Photography",
        "Spanish","Sport"
    ]

    available_subjects = [c for c in subject_cols if c in df.columns]

    selected_subject = st.sidebar.selectbox("Subject (optional)", ["All Subjects"] + available_subjects, key="y10_subject")

    filtered_df = df.copy()

    if selected_form:
        filtered_df = filtered_df[filtered_df["Form Group"].astype(str).isin(selected_form)]
    if selected_math:
        filtered_df = filtered_df[filtered_df["Maths Set"].astype(str).isin(selected_math)]
    if selected_subject != "All Subjects":
        filtered_df = filtered_df[
            filtered_df[selected_subject].notna() &
            (filtered_df[selected_subject].astype(str).str.strip() != "")
        ]

    st.sidebar.divider()
    report_option = st.sidebar.radio(
        "Select Report Detail",
        ["Base Passport (No Details)", "Short Report (KS3 & Home Life)", "Detailed Report (All Subjects)"]
    )

    # --- PRINT MODE TOGGLE ---
    st.sidebar.divider()
    print_mode = st.sidebar.toggle("🖨️ Enable Print View", value=False)
    
    if print_mode:
        inject_print_css()
        st.success("🖨️ **Print View Ready!** Press `Ctrl + P` (Windows) or `Cmd + P` (Mac) and select **Save as PDF** to generate your document.")

    mode = "None"
    if report_option == "Short Report (KS3 & Home Life)":
        mode = "Short"
    elif report_option == "Detailed Report (All Subjects)":
        mode = "Detailed"

    st.subheader(f"Showing {len(filtered_df)} Students")
    
    render_photo_grid(filtered_df, "Year 10", num_cols=5)
    
    st.divider()
    st.subheader("📄 Detailed Passports")
    
    for _, row in filtered_df.iterrows():
        # Pass the print_mode setting to the cards
        render_student_card(row, "Year 10", show_projected=True, report_type=mode, is_print_mode=print_mode)

# ------------------ ANALYTICS ------------------
elif page == "Analytics":
    analytics(df_y7, df_y10)
