import streamlit as st
import pandas as pd
import os
from PIL import Image
import requests
from io import StringIO

st.set_page_config(page_title="Virtual Student MIS", layout="wide")

# ---------------------------
# DATA SOURCES
# ---------------------------
YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=0&single=true"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=214766920&single=true"

COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"]

# ---------------------------
# SAFE DATA LOADER
# ---------------------------
@st.cache_data(ttl=30)
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
        st.error("Data loading failed")
        st.exception(e)
        return pd.DataFrame()

# ---------------------------
# COLUMN DETECTION ENGINE
# ---------------------------
def find_column(df, keywords):
    for col in df.columns:
        col_l = col.lower()
        for k in keywords:
            if k.lower() in col_l:
                return col
    return None

# ---------------------------
# PHOTO HANDLER (LEFT / RIGHT CROP)
# ---------------------------
def display_student_photo(name, cohort):
    folder = "photos"
    if not os.path.exists(folder):
        st.caption("No photo folder")
        return

    safe = name.lower().replace(".", "")
    files = {f.lower(): f for f in os.listdir(folder)}

    if f"{safe}.png" not in files:
        st.caption("No photo")
        return

    img = Image.open(os.path.join(folder, files[f"{safe}.png"]))
    w, h = img.size

    trim = int(h * 0.08)
    top, bottom = trim, h - trim

    if cohort == "Year 7":
        crop = (0, top, w // 2, bottom)
    else:
        crop = (w // 2, top, w, bottom)

    st.image(img.crop(crop), width=220)

# ---------------------------
# SAFE VALUE FETCH
# ---------------------------
def get_val(row, keys):
    for k in keys:
        for col in row.index:
            if k.lower() in col.lower() and str(row[col]).strip():
                return row[col]
    return "N/A"

# ---------------------------
# DATA VALIDATION PANEL
# ---------------------------
def data_validation(df):
    st.subheader("📊 Data Validation")

    st.write("### Column Overview")

    col_data = []
    for col in df.columns:
        missing = df[col].isna().sum()
        col_data.append([col, len(df), missing])

    st.dataframe(pd.DataFrame(col_data, columns=["Column", "Total Rows", "Missing"]))

# ---------------------------
# SMART FILTER BUILDER
# ---------------------------
def build_filters(df):
    st.sidebar.subheader("🧭 Smart Filters")

    filters = {}

    possible_filters = {
        "Maths Set": ["maths set", "maths", "set maths"],
        "English Set": ["english set", "english"],
        "Science Set": ["science set", "science"],
        "Tutor Group": ["tutor", "form"],
        "Year Group": ["year"]
    }

    for label, keys in possible_filters.items():
        col = find_column(df, keys)

        if col:
            options = sorted(df[col].astype(str).unique())
            filters[label] = st.sidebar.selectbox(label, options)
            df = df[df[col].astype(str) == filters[label]]

    return df

# ---------------------------
# PASSPORT VIEW
# ---------------------------
def render_passport(df, cohort):
    st.title(f"{cohort} Student Passports")

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

            info = {
                "Gender": ["gender"],
                "SEN Status": ["sen status", "send"],
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

# filters
df_filtered = build_filters(df)

st.write("---")

# validation
if st.checkbox("📊 Show Data Validation"):
    data_validation(df)

st.write("---")

# passports
render_passport(df_filtered, cohort)
