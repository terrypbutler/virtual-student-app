import streamlit as st
import pandas as pd
import os
from PIL import Image
import requests
from io import StringIO

st.set_page_config(page_title="Virtual Student MIS", layout="wide")

# ---------------------------
# DATA SOURCES (REPLACE THESE)
# ---------------------------
YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=0&single=true"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=214766920&single=true"

COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"]

# ---------------------------
# SAFE DATA LOADER (CRASH PROOF)
# ---------------------------
@st.cache_data(ttl=60)
def load_data(url):
    try:
        r = requests.get(url)
        r.raise_for_status()

        df = pd.read_csv(
            StringIO(r.text),
            engine="python",
            on_bad_lines="skip"
        )

        df.columns = df.columns.str.strip()

        drop = [c for c in COLUMNS_TO_HIDE if c in df.columns]
        if drop:
            df = df.drop(columns=drop)

        return df.fillna("")

    except Exception as e:
        st.error("❌ Data failed to load")
        st.exception(e)
        return pd.DataFrame()

# ---------------------------
# SAFE COLUMN FINDER
# ---------------------------
def find_column(df, keywords):
    for col in df.columns:
        col_clean = col.strip().lower()
        for k in keywords:
            if k.lower() == col_clean:
                return col
    return None

# ---------------------------
# PHOTO DISPLAY (LEFT / RIGHT CROPPING)
# ---------------------------
def display_student_photo(name, cohort):
    folder = "photos"

    if not os.path.exists(folder):
        st.caption("No photo folder")
        return

    safe = name.lower().replace(".", "")
    files = {f.lower(): f for f in os.listdir(folder)}

    key = f"{safe}.png"

    if key not in files:
        st.caption("No photo")
        return

    img = Image.open(os.path.join(folder, files[key]))
    w, h = img.size

    trim = int(h * 0.08)
    top, bottom = trim, h - trim

    if cohort == "Year 7":
        crop = (0, top, w // 2, bottom)
    else:
        crop = (w // 2, top, w, bottom)

    st.image(img.crop(crop), width=220)

# ---------------------------
# SAFE VALUE GETTER
# ---------------------------
def get_val(row, keywords):
    for col in row.index:
        for k in keywords:
            if k.lower() in col.lower():
                val = str(row[col]).strip()
                if val:
                    return val
    return "N/A"

# ---------------------------
# DATA VALIDATION PANEL
# ---------------------------
def data_validation(df):
    st.subheader("📊 Data Health Check")

    st.write("### Column Overview")

    summary = []
    for col in df.columns:
        missing = df[col].isna().sum()
        summary.append([col, len(df), missing])

    st.dataframe(pd.DataFrame(summary, columns=["Column", "Rows", "Missing"]))

# ---------------------------
# FILTER SYSTEM (SAFE)
# ---------------------------
def apply_filters(df):
    st.sidebar.subheader("🧭 Filters")

    filters = {
        "Maths Set": ["maths set", "maths"],
        "English Set": ["english set", "english"],
        "Science Set": ["science set", "science"],
        "Tutor Group": ["tutor", "form"],
        "Year Group": ["year"]
    }

    filtered = df.copy()

    for label, keys in filters.items():
        col = find_column(filtered, keys)

        if col:
            options = sorted([x for x in filtered[col].unique() if str(x).strip()])

            if len(options) > 1:
                choice = st.sidebar.selectbox(label, ["All"] + options)

                if choice != "All":
                    filtered = filtered[filtered[col] == choice]

    return filtered

# ---------------------------
# PASSPORT RENDERER
# ---------------------------
def render_passports(df, cohort):
    st.title(f"🎓 {cohort} Student Passports")

    for _, row in df.iterrows():

        name = row.get("Full Name", "Unknown")
        dob = row.get("DoB", "")
        header = f"{name} ({dob})" if dob else name

        with st.expander(header):

            c1, c2 = st.columns([3, 1])

            with c1:
                st.markdown(f"### {header}")

            with c2:
                display_student_photo(name, cohort)

            st.write("---")

            info = {
                "Form Group": ["form", "tutor"],
                "Gender": ["gender"],
                "SEN Status": ["sen", "send"],
                "Ethnicity": ["ethnicity"],
                "EAL": ["eal"],
                "Disadvantaged": ["pupil premium", "disadvantaged"],
                "SATs Reading": ["reading"],
                "SATs Maths": ["maths"]
            }

            for label, keys in info.items():
                col1, col2 = st.columns([1, 2])
                col1.markdown(f"**{label}**")
                col2.markdown(get_val(row, keys))

# ---------------------------
# MAIN APP
# ---------------------------
st.title("🎓 Virtual Student MIS System")

cohort = st.radio("Select Cohort", ["Year 7", "Year 9"], horizontal=True)

df = load_data(YEAR_7_URL if cohort == "Year 7" else YEAR_9_URL)

if df.empty:
    st.stop()

df = apply_filters(df)

st.write("---")

if st.checkbox("📊 Data Health Check"):
    data_validation(df)

st.write("---")

search = st.text_input("🔍 Search student name")

if search:
    df = df[df["Full Name"].str.contains(search, case=False, na=False)]

st.write("---")

render_passports(df, cohort)
