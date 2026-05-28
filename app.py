import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?output=csv"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pub?gid=214766920&single=true&output=csv"

@st.cache_data(ttl=10)
def load_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data.fillna("")

def display_student_photo(student_name, cohort, is_grid=False):
    safe_name = str(student_name).strip().replace(".", "")
    folder_path = "photos" 
    if not os.path.exists(folder_path): return
    
    all_files = os.listdir(folder_path)
    file_map = {f.lower(): f for f in all_files} 
    target = f"{safe_name.lower()}.png"
    
    if target in file_map:
        img = Image.open(os.path.join(folder_path, file_map[target]))
        w, h = img.size
        trim = int(h * 0.08)
        box = (w // 2, trim, w, h - trim) if cohort == "Year 9" else (0, trim, w // 2, h - trim)
        st.image(img.crop(box), width=100 if is_grid else 220)
    else:
        st.caption("*(No photo)*")

def render_student_table(row):
    st.markdown(f"""
    <table style="width:100%; border: 1px solid #ddd; border-collapse: collapse; background: white;">
        <tr><td style="padding: 10px;"><strong>Form:</strong> {row.get('Form Group', 'N/A')}</td><td style="padding: 10px;"><strong>Gender:</strong> {row.get('Gender', 'N/A')}</td></tr>
        <tr><td style="padding: 10px;"><strong>SEN:</strong> {row.get('SEN Status', 'N/A')}</td><td style="padding: 10px;"><strong>Detail:</strong> {row.get('SEND detail', 'N/A')}</td></tr>
        <tr><td style="padding: 10px;"><strong>Ethnicity:</strong> {row.get('Ethnicity', 'N/A')}</td><td style="padding: 10px;"><strong>EAL:</strong> {row.get('EAL', 'N/A')}</td></tr>
        <tr><td colspan="2" style="padding: 10px;"><strong>Disadvantaged:</strong> {row.get('Disadvantaged (PP)', 'N/A')}</td></tr>
        <tr><td style="padding: 10px;"><strong>Reading:</strong> {row.get('SATs Reading', 'N/A')}</td><td style="padding: 10px;"><strong>Maths:</strong> {row.get('SATs Maths', 'N/A')}</td></tr>
    </table>
    """, unsafe_allow_html=True)

# Main App Layout
st.title("🎓 Virtual Student Intake Dashboard")
selected_cohort = st.radio("📅 Select Cohort:", ["Year 7", "Year 9"], horizontal=True)
df = load_data(YEAR_7_URL if selected_cohort == "Year 7" else YEAR_9_URL)

view_type = st.radio("🔍 Group By:", ["Maths Set", "Tutor Group"], horizontal=True)
target_col = "Maths Set" if view_type == "Maths Set" else next((c for c in df.columns if c in ["Form Group", "Tutor Group", "Form Tutor", "Tutor"]), "Form Group")

selected_set = st.selectbox(f"🎯 Select {view_type}:", sorted(df[target_col].dropna().unique().tolist()))
filtered_df = df[df[target_col] == selected_set]

# ✨ RAW DATA TOGGLE (Restored)
if st.checkbox(f"🔍 View Raw {selected_cohort} Data Matrix"):
    st.dataframe(filtered_df, use_container_width=True)

st.write("---")

# Report Tabs
tab1, tab2, tab3 = st.tabs(["🖼️ Photo Grid", "📄 Transition Passport", "📊 Progress Reports"])

with tab1:
    cols = st.columns(8)
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 8]:
            display_student_photo(row["Full Name"], selected_cohort, is_grid=True)
            st.caption(row["Full Name"])

with tab2:
    for _, row in filtered_df.iterrows():
        with st.expander(f"👤 {row['Full Name']}"):
            c1, c2 = st.columns([3, 1])
            with c1: st.markdown(f"### {row['Full Name']} ({row.get('DoB', '')})"); render_student_table(row)
            with c2: display_student_photo(row['Full Name'], selected_cohort)

with tab3:
    for _, row in filtered_df.iterrows():
        with st.expander(f"📊 {row['Full Name']}"):
            m1, m2 = st.columns(2)
            m1.metric("Current Grade", row.get('Current Grade', 'N/A'))
            m2.metric("Target Grade", row.get('Target Grade', 'N/A'))
            render_student_table(row)
            subj_cols = [c for c in df.columns if any(x in c.lower() for x in ["subject", "grade", "score"]) and not any(x in c.lower() for x in ["target", "current", "set", "maths", "reading"])]
            if subj_cols: st.dataframe(row[subj_cols], use_container_width=True)
