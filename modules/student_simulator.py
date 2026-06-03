import streamlit as st
import google.generativeai as genai
from modules.photo_utils import display_student_photo

def get_flexible_text(row, possible_names):
    """Helper to safely extract data from the row."""
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                if val.endswith(".0"): val = val[:-2]
                return val
    return "None recorded"

def render_simulator(df, cohort):
    st.subheader("🤖 Virtual Student Simulator")
    
    # 1. API Configuration
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing. Please add it to your secrets.toml file.")
        return
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 2. Student Selection
    student_list = df["Full Name"].tolist()
    selected_student = st.selectbox("Select Student to Roleplay:", student_list)
    
    if not selected_student:
        return
        
    row = df[df["Full Name"] == selected_student].iloc[0]
    
    # 3. Extract Context for the AI
    age = "11" if cohort == "Year 7" else "15"
    sen = get_flexible_text(row, ["SEN Status", "SEND Status", "SEN Detail"])
    home_life = get_flexible_text(row, ["Home Life & Interests", "Home Life", "Interests"])
    predicted = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
    suspensions = get_flexible_text(row, ["Suspension days", "Suspensions"])
    eal = get_flexible_text(row, ["EAL", "EAL Status"])
    
    st.markdown("---")
    
    # --- UI Layout ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            display_student_photo(selected_student, cohort)
            st.markdown(f"**Target Profile:**")
            st.caption(f"**SEN:** {sen}")
            st.caption(f"**EAL:** {eal}")
            st.caption(f"**Grade:** {predicted}")
            st.caption(f"**Home:** {home_life[:60]}...")
            
        scenario = st.radio("Scenario:", ["End of Lesson", "Corridor Behavior", "Struggling with Task"])
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state[f"chat_{selected_student}"] = []
            st.rerun()

    with col2:
        # 4. Chat History Initialization
        chat_key = f"chat_{selected_student}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
            
        # Display previous chat messages
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # 5. The Chat Input & AI Generation
        teacher_input = st.chat_input(f"Say something to {selected_student}...")
        
        if teacher_input:
            # Show the teacher's message instantly
            st.session_state[chat_key].append({"role": "user", "content": teacher_input})
            with st.chat_message("user"):
                st.write(teacher_input)

            # Build the continuous transcript so the AI remembers the conversation!
            transcript = "\n".join([f"{'Teacher' if m['role']=='user' else selected_student}: {m['content']}" for m in st.session_state[chat_key]])

            # Build the invisible System Prompt
            system_prompt = f"""
            You are roleplaying as a {age}-year-old UK secondary school student named {selected_student}.
            Here is your background data:
            - Special Educational Needs (SEN): {sen}
            - English as Additional Language (EAL): {eal}
            - General Academic Level: {predicted}
            - Home Life and Interests: {home_life}
            - Suspensions: {suspensions}
            
            The current scenario is: {scenario}.
            
            Here is the conversation transcript so far:
            {transcript}
            
            Respond to the teacher's last statement as {selected_student}. 
            Respond exactly how a student with your profile would respond. 
            Do NOT break character. Do NOT be overly polite if your profile suggests behavior issues.
            Keep your response short (1 to 3 sentences maximum) as a real teenager would.
            """

            # Call the AI (Using the Pro model for deep emotional/behavioral nuance)
            with st.spinner(f"{selected_student} is thinking..."):
                try:
                    model = genai.GenerativeModel('gemini-2.5-pro')
                    response = model.generate_content(system_prompt)
                    
                    # Save and show the student's response
                    st.session_state[chat_key].append({"role": "assistant", "content": response.text})
                    with st.chat_message("assistant"):
                        st.write(response.text)
                except Exception as e:
                    st.error(f"API Error: {e}")
