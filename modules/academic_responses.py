import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
from modules.photo_utils import display_student_photo

def get_flexible_text(row, possible_names):
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                if val.endswith(".0"): val = val[:-2]
                return val
    return "Unknown"

def render_academic_responses(df, cohort):
    st.subheader("🎓 AfL Simulator: Whole Class Whiteboards")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing.")
        return
        
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # 1. The Input Area
    st.markdown("### 1. Present the Material")
    teacher_question = st.text_area("Ask the class a question (e.g., 'What is the capital of France?' or 'Solve for x in the image'):")
    uploaded_file = st.file_uploader("Upload a resource (optional)", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("### 2. Collect Responses")
    
    if st.button("📝 Show All Mini-Whiteboards", use_container_width=True, type="primary"):
        if not teacher_question:
            st.warning("Please ask a question first!")
            return
            
        with st.spinner("Students are writing their answers (this takes about 10 seconds)..."):
            try:
                # Build a concise summary of the class to send to the AI
                student_profiles = []
                for _, row in df.iterrows():
                    name = row.get("Full Name")
                    grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
                    sen = get_flexible_text(row, ["SEN Status", "SEND Status"])
                    eal = get_flexible_text(row, ["EAL", "EAL Status"])
                    student_profiles.append(f"- {name} (Target: {grade}, SEN: {sen}, EAL: {eal})")
                    
                profiles_text = "\n".join(student_profiles)
                
                # Build the prompt forcing JSON output
                prompt = f"""
                You are simulating a class of students writing answers on mini-whiteboards.
                The teacher has asked: "{teacher_question}"
                
                Here is the class list:
                {profiles_text}
                
                Generate a realistic, short answer (maximum 6 words) for EACH student based on their profile. 
                Higher target grades should be more accurate. Lower target grades might have common misconceptions, spelling errors, or blank answers. EAL students might use simplified phrasing.
                
                Return ONLY a JSON dictionary where the keys are the exact student names and the values are their answers.
                """
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                contents = [prompt]
                
                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    contents.append(image)
                    
                # Force Gemini to return perfect JSON data instead of conversational text
                response = model.generate_content(
                    contents, 
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # Convert the AI's JSON text into a Python Dictionary
                answers = json.loads(response.text)
                
                # --- RENDER THE CLASSROOM GRID ---
                st.markdown("---")
                
                # We use 5 columns across
                num_cols = 5
                for i in range(0, len(df), num_cols):
                    cols = st.columns(num_cols)
                    row_students = df.iloc[i : i + num_cols]
                    
                    for col, (_, row) in zip(cols, row_students.iterrows()):
                        with col:
                            name = row.get("Full Name")
                            
                            # 1. Show the Photo and Name
                            display_student_photo(name, cohort)
                            st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 13px; margin: 4px 0;'>{name}</div>", unsafe_allow_html=True)
                            
                            # 2. Grab their specific answer from the dictionary
                            student_answer = answers.get(name, "?")
                            
                            # 3. Draw the Whiteboard Box underneath
                            st.markdown(f"""
                                <div style='background-color: #ffffff; border: 3px solid #2C3E50; border-radius: 6px; 
                                            padding: 10px 5px; margin-bottom: 20px; min-height: 70px; 
                                            display: flex; align-items: center; justify-content: center; 
                                            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>
                                    <span style='color: #1a1a1a; font-size: 14px; font-weight: bold; text-align: center;'>
                                        {student_answer}
                                    </span>
                                </div>
                            """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Something went wrong generating the answers. Error: {e}")
