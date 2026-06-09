import streamlit as st
import google.generativeai as genai
import json
from modules.photo_utils import display_student_photo

# Import your ElevenLabs function from the other file
try:
    from modules.academic_responses import get_elevenlabs_audio
except ImportError:
    st.error("⚠️ Could not find get_elevenlabs_audio in modules.academic_responses")

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
    # --- HEADER & MASTER TOGGLE ---
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("🤖 Virtual Student Simulator")
    with col_header2:
        # This toggle controls whether audio is generated!
        enable_voice = st.toggle("🔊 Voice Audio", value=True, key="sim_voice_toggle")
        
    # 1. API Configuration
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing.")
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
        # --- RENDER SAFE AUDIO PLAYER ---
        if "latest_audio_sim" in st.session_state:
            st.audio(st.session_state["latest_audio_sim"], format="audio/mp3", autoplay=True)
            del st.session_state["latest_audio_sim"]

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
            st.session_state[chat_key].append({"role": "user", "content": teacher_input})
            with st.chat_message("user"):
                st.write(teacher_input)

            transcript = "\n".join([f"{'Teacher' if m['role']=='user' else selected_student}: {m['content']}" for m in st.session_state[chat_key]])

            system_prompt = f"""
            You are roleplaying as a {age}-year-old UK student named {selected_student}.
            Data: SEN: {sen} | EAL: {eal} | Grade: {predicted} | Home: {home_life} | Suspensions: {suspensions}
            Scenario: {scenario}.
            
            Transcript:
            {transcript}
            
            CRITICAL RULES:
            1. Respond as {selected_student}. Keep it short (1-3 sentences).
            2. Determine the student's current emotion based on the scenario and teacher's prompt. Pick ONE: [neutral, angry, defensive, sad, bored, hesitant, excited, eager].
            3. You MUST return your response as a raw JSON object with two keys: "dialogue" and "emotion".
            
            Example Format:
            {{"dialogue": "I don't know why you're picking on me, sir. I wasn't even talking.", "emotion": "defensive"}}
            """

            with st.spinner(f"{selected_student} is reacting..."):
                try:
                    model = genai.GenerativeModel('gemini-3.5-flash')
                    response = model.generate_content(system_prompt, generation_config={"response_mime_type": "application/json"})
                    
                    ai_data = json.loads(response.text)
                    reply_text = ai_data.get("dialogue", "...")
                    current_emotion = ai_data.get("emotion", "neutral")
                    
                    st.session_state[chat_key].append({"role": "assistant", "content": reply_text})
                    st.toast(f"Student Mood: {current_emotion.upper()} 🎭")
                    
                    # --- TOGGLE LOGIC: ONLY GENERATE AUDIO IF SWITCH IS ON ---
                    if enable_voice:
                        student_voice_id = row.get("Voice_Name", "JBFqnCBsd6RMkjVDRZzb")
                        audio_bytes = get_elevenlabs_audio(reply_text, student_voice_id)
                        
                        if audio_bytes is None:
                            st.stop() 
                        else:
                            st.session_state["latest_audio_sim"] = audio_bytes
                    
                    st.rerun() 
                        
                except Exception as e:
                    st.error(f"API/Parsing Error: {e}")
