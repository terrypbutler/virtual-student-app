# config.py

YEAR_7_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=0&single=true"
YEAR_9_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRWjfO_UYUARLvEtyHGb0tW35YcgG0R6175_MvHnKkCSx-o6Aq7hvFOpjiobdoh7hmjULvIEdRWX8Ik/pubhtml?gid=214766920&single=true"

PHOTO_FOLDER = "photos"
PHOTO_WIDTH = 220
CACHE_TTL = 30

COLUMNS_TO_HIDE = [
    "Picture",
    "First Name",
    "Surname Initial",
    "Student ID"
]

FIELD_MAP = {
    "form_group": ["Form Tutor", "Tutor", "Form Group", "Tutor Group"],
    "gender": ["Gender"],
    "sen_status": ["SEN Status", "SEND Status"],
    "sen_detail": ["SEND detail", "SEN detail"],
    "ethnicity": ["Ethnicity"],
    "eal": ["EAL", "EAL Status"],
    "pp": ["Premium", "Disadvantaged", "Pupil Premium", "Disadvantaged (PP)"],
    "reading": ["SATs Reading", "SAT's Reading", "Reading Score"],
    "maths": ["SATs Maths", "SAT's Maths", "Maths Score"]
}

COLUMN_ALIASES = {
    "SAT's Maths": "SATs Maths",
    "Maths Score": "SATs Maths",
    "SAT's Reading": "SATs Reading",
    "Reading Score": "SATs Reading"
