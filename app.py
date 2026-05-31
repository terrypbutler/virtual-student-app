import streamlit as st
import pandas as pd
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

    # --- FILTERS ---
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

    # --- APPLY FILTERS ---
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

    # --- CALCULATE METRICS ---
    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN", "0", "0.0"]
    
    def count_active(col_names):
        col = next((c for c in df.columns if c.strip().lower() in [n.lower() for n in col_names]), None)
        if col:
            return df[col].astype(str).str.upper().apply(lambda x: x.strip() not in ignore_list).sum()
        return 0

    sen_count = count_active(["SEN Status", "SEND Status"])
    eal_count = count_active(["EAL", "EAL Status"])
    
    # Added "Disadvantaged (PP)" exactly as it appears
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

    # --- GRAPHS WITH NUMERICAL BATCHING ---
    st.subheader("📈 KS2 / SATs Performance")
    g1, g2 = st.columns(2)
    
    read_col = next((c for c in df.columns if c.strip().lower() in ["ks2 read", "ks2 reading", "sats reading", "reading score"]), None)
    math_col = next((c for c in df.columns if c.strip().lower() in ["ks2 maths", "ks2 math", "sats maths", "maths score"]), None)
    
    with g1:
        if math_col:
            st.markdown("**Maths Distribution (Batches of 5)**")
            math_nums = pd.to_numeric(df[math_col], errors='coerce').dropna()
            
            if not math_nums.empty:
                min_score = int((math_nums.min() // 5) * 5)
                max_score = int((math_nums.max() // 5) * 5) + 5
                bins = list(range(min_score, max_score + 5, 5))
                labels = [f"{bins[i]}-{bins[i]+4}" for i in range(len(bins)-1)]
                
                math_binned = pd.cut(math_nums, bins=bins, labels=labels, right=False)
                math_counts = math_binned.value_counts().sort_index()
                st.bar_chart(math_counts)
            else:
                st.caption("*(No numeric Maths data available)*")
        else:
            st.caption("*(No Maths data available)*")
            
    with g2:
        if read_col:
            st.markdown("**Reading Distribution (Batches of 5)**")
            read_nums = pd.to_numeric(df[read_col], errors='coerce').dropna()
            
            if not read_nums.empty:
                min_score = int((read_nums.min() // 5) * 5)
                max_score = int((read_nums.max() // 5) * 5) + 5
                bins = list(range(min_score, max_score + 5, 5))
                labels = [f"{bins[i]}-{bins[i]+4}" for i in range(len(bins)-1)]
                
                read_binned = pd.cut(read_nums, bins=bins, labels=labels, right=False)
                read_counts = read_binned.value_counts().sort_index()
                st.bar_chart(read_counts)
            else:
                st.caption("*(No numeric Reading data available)*")
        else:
            st.caption("*(No Reading data available)*")

    st.write("---")
    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True)


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

    report_option = st.sidebar.radio(
        "Select Report Detail",
        ["Base Passport (No Details)", "Short Report (Portrait & Home Life)", "Detailed Report (All Subjects)"]
    )

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
        render_student_card(row, "Year 7", show_projected=True, report_type=mode)

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

    report_option = st.sidebar.radio(
        "Select Report Detail",
        ["Base Passport (No Details)", "Short Report (KS3 & Home Life)", "Detailed Report (All Subjects)"]
    )

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
        render_student_card(row, "Year 10", show_projected=True, report_type=mode)

# ------------------ ANALYTICS ------------------
elif page == "Analytics":
    analytics(df_y7, df_y10)
