import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Virtual Student Intake", layout="wide")

# ---------------------------
# URLs for Google Sheets CSV
# ---------------------------
YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=0&single=true"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=214766920&single=true"

COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"] 

# ---------------------------
# Data Loader
# ---------------------------
@st.cache_data(ttl=10)
def load_data(url):
    import pandas as pd
    import requests
    from io import StringIO

    try:
        # --- Download raw CSV safely ---
        response = requests.get(url)
        response.raise_for_status()
        csv_text = response.text

        # --- Clean problematic line breaks inside rows ---
        cleaned_lines = []
        for line in csv_text.splitlines():
            # Skip completely broken empty lines
            if not line.strip():
                continue
            cleaned_lines.append(line)

        cleaned_csv = "\n".join(cleaned_lines)

        # --- Read CSV in SAFE mode ---
        data = pd.read_csv(
            StringIO(cleaned_csv),
            engine="python",          # more forgiving than C engine
            on_bad_lines="skip",      # skips broken rows automatically
            quotechar='"',
            skipinitialspace=True
        )

        # --- Clean headers ---
        data.columns = data.columns.str.strip()

        # --- Remove hidden system columns ---
        COLUMNS_TO_HIDE = ["Picture", "First Name", "Surname Initial", "Student ID"]
        cols_to_drop = [col for col in COLUMNS_TO_HIDE if col in data.columns]
        if cols_to_drop:
            data = data.drop(columns=cols_to_drop)

        # --- Normalize empty values ---
        data = data.fillna("")

        return data

    except Exception as e:
        import streamlit as st
        st.error("⚠️ Data loading failed — using fallback empty dataset")
        st.exception(e)

        # safe fallback so app never crashes
        return pd.DataFrame()

# ---------------------------
# Display student photo (left/right crop)
# ---------------------------
def display_student_photo(student_name, cohort):
    safe_name = str(student_name).strip().replace(".", "")
    folder_path = "photos"
    if not os.path.exists(folder_path):
        st.caption("*(Error: 'photos' folder not found)*")
        return

    try:
        all_files = os.listdir(folder_path)
        file_map = {f.lower(): f for f in all_files}
        target_filename = f"{safe_name.lower()}.png"

        if target_filename in file_map:
            img = Image.open(os.path.join(folder_path, file_map[target_filename]))
            width, height = img.size
            trim_amount = int(height * 0.08)
            top_edge = trim_amount
            bottom_edge = height - trim_amount

            if cohort == "Year 9":
                crop_box = (width // 2, top_edge, width, bottom_edge)
            else:
                crop_box = (0, top_edge, width // 2, bottom_edge)

            st.image(img.crop(crop_box), width=220)
        else:
            st.caption(f"*(Missing photo: {safe_name}.png)*")
    except Exception:
        st.caption("*(File error or invalid image)*")

# ---------------------------
# Helper: get first valid value from multiple keys
# ---------------------------
def get_val(row_data, keys):
    keys_lower = [k.lower() for k in keys]
    for col in row_data.index:
        if col.lower() in keys_lower and str(row_data[col]).strip() != "":
            return str(row_data[col])
    return "N/A"

# ---------------------------
# Render Year 7 Passports
# ---------------------------
def render_y7_passports(filtered_df):
    st.markdown("### 📄 Year 7 Passports")
    for _, row in filtered_df.iterrows():
        s_name = str(row.get("Full Name", "Unknown Student"))
        s_dob = str(row.get("DoB", "")).strip()
        header_text = f"{s_name} ({s_dob})" if s_dob else s_name

        with st.expander(f"👤 {header_text} — Year 7 Passport"):
            title_col, photo_col = st.columns([3, 1])
            with title_col:
                st.markdown(f"### **{header_text}**")
            with photo_col:
                display_student_photo(s_name, "Year 7")

            st.write("---")
            info = {
                "Form Group": ["Form Tutor", "Tutor", "Form Group"],
                "Gender": ["Gender"],
                "SEN Status": ["SEN Status", "SEND Status"],
                "SEN Detail": ["SEND detail", "SEN detail"],
                "Ethnicity": ["Ethnicity"],
                "EAL": ["EAL", "EAL Status"],
                "Disadvantaged": ["Premium", "Disadvantaged", "Pupil Premium", "Disadvantaged (PP)"],
                "SATs Reading": ["SATs Reading", "SAT's Reading", "Reading Score"],
                "SATs Maths": ["SATs Maths", "SAT's Maths", "Maths Score"]
            }

            for label, keys in info.items():
                value = get_val(row, keys)
                col1, col2 = st.columns([1, 2])
                col1.markdown(f"**{label}:**")
                col2.markdown(str(value))

# ---------------------------
# Render Year 9 Passports
# ---------------------------
def render_y9_passports(filtered_df):
    st.markdown("### 📄 Year 9 Passports")
    for _, row in filtered_df.iterrows():
        s_name = str(row.get("Full Name", "Unknown Student"))
        s_dob = str(row.get("DoB", "")).strip()
        header_text = f"{s_name} ({s_dob})" if s_dob else s_name

        with st.expander(f"👤 {header_text} — Year 9 Passport"):
            title_col, photo_col = st.columns([3, 1])
            with title_col:
                st.markdown(f"### **{header_text}**")
            with photo_col:
                display_student_photo(s_name, "Year 9")

            st.write("---")
            info = {
                "Form Group": ["Form Tutor", "Tutor", "Form Group"],
                "Gender": ["Gender"],
                "SEN Status": ["SEN Status", "SEND Status"],
                "SEN Detail": ["SEND detail", "SEN detail"],
                "Ethnicity": ["Ethnicity"],
                "EAL": ["EAL", "EAL Status"],
                "Disadvantaged": ["Premium", "Disadvantaged", "Pupil Premium", "Disadvantaged (PP)"],
                "SATs Reading": ["SATs Reading", "SAT's Reading", "Reading Score"],
                "SATs Maths": ["SATs Maths", "SAT's Maths", "Maths Score"]
            }

            for label, keys in info.items():
                value = get_val(row, keys)
                col1, col2 = st.columns([1, 2])
                col1.markdown(f"**{label}:**")
                col2.markdown(str(value))

# ---------------------------
# Main App
# ---------------------------
try:
    st.title("🎓 Virtual Student Intake Dashboard")
    st.caption("Live simulation data framework for teacher training modules.")

    selected_cohort = st.radio("📅 Select Cohort:", ["Year 7", "Year 9"], horizontal=True)
    st.write("---")

    df = load_data(YEAR_7_URL if selected_cohort=="Year 7" else YEAR_9_URL)

    # Group / Set view
    view_type = st.radio("🔍 Group View By:", ["Maths Set", "Tutor Group"], horizontal=True)
    TARGET_COLUMN = "Maths Set" if view_type=="Maths Set" else next((col for col in df.columns if col in ["Form Group","Tutor Group","Form Tutor","Tutor"]), "Form Group")
    available_sets = sorted(df[TARGET_COLUMN].dropna().unique().tolist())
    selected_set = st.selectbox(f"🎯 Select {selected_cohort} {view_type}:", available_sets)
    filtered_df = df[df[TARGET_COLUMN] == selected_set]

    st.write("---")

    # ---------------------------
    # Render Passports
    # ---------------------------
    if selected_cohort == "Year 7":
        render_y7_passports(filtered_df)
    else:
        render_y9_passports(filtered_df)

except Exception as e:
    st.error("Error running application. Check data and column names.")
    st.exception(e)
