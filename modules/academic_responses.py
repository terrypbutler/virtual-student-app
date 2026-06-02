import streamlit as st
import google.generativeai as genai
import json
import time
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

def fetch_ai_answers(question, student_subset, instructions, uploaded_file, cohort, subject):
    """Handles batch generations (Whiteboards, Exit Tickets, Hands Up)"""
    age_context = "11 to 12 years old" if cohort == "Year 7" else "14 to 15 years old"
    
    profiles = []
    for _, row in student_subset.iterrows():
        name = row.get("Full Name")
        grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
        sen = get_flexible_text(row, ["SEN Status", "SEND Status"])
        eal = get_flexible_text(row, ["EAL", "EAL Status"])
        math_score = get_flexible_text(row, ["KS2 Maths", "KS2 Math", "SATs Maths"])
        read_score = get_flexible_text(row, ["KS2 Read", "KS2 Reading", "SATs Reading"])
        suspensions = get_flexible_text(row, ["Suspension days", "Suspensions"])
        home_life = get_flexible_text(row, ["Home Life & Interests", "Home Life"])
        profiles.append(f"- {name} | Target: {grade} | SEN: {sen} | EAL: {eal} | KS2 Math: {math_score} | KS2 Read: {read_score} | Susp: {suspensions} | Home: {home_life}")
        
    profiles_text = "\n".join(profiles)
    
    prompt = f"""
    A trainee teacher is conducting a {subject} lesson for a class of {cohort} students (approximate age: {age_context}).
    The teacher has asked the class: "{question}"
    
    Here is the detailed data for the specific students answering:
    {profiles_text}
    
    {instructions}
    
    CRITICAL PEDAGOGICAL CONSTRAINTS:
    1. Ability Match: Scale vocabulary, accuracy, and depth to their Target Grade and KS2/SATs scores. 
    2. Deep Misconceptions: Inject realistic, {subject}-specific misconceptions or partial misunderstandings for lower grades.
    3. Attitude: Factor in suspensions and home context to randomly assign a mood.
    
    CRITICAL: Format math using standard text (e.g., x² or x^2), NO LaTeX.
    CRITICAL: Return ONLY a valid JSON dictionary where keys are exact student names and values are their answers.
    """
    
    for attempt in range(3):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            contents = [prompt]
            if uploaded_file is not None: contents.append(Image.open(uploaded_file))
                
            response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text.replace("```json", "").replace("```", "").strip())
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                st.toast(f"🚦 AI Speed Limit hit. Auto-retrying in 20 seconds...")
                time.sleep(20)
            elif attempt == 2:
                st.error("🚦 AI exhausted. Please wait 60 seconds.")
                return {}
    return {}

def render_academic_responses(df, cohort, subject="General"):
    st.subheader(f"🎓 AfL Simulator: {subject} Questioning")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing.")
        return
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # --- 1. THE INPUT AREA ---
    st.markdown("### 1. Present the Material")
    teacher_question = st.text_area("Ask the class your opening question:")
    uploaded_file = st.file_uploader("Upload a resource (optional)", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Class Resource", use_container_width=True)
    
    # --- 2. THE MODE SELECTOR ---
    st.markdown("---")
    st.markdown("### 2. Select Questioning Strategy")
    mode = st.radio("Strategy:", [
        "📝 Mini-Whiteboards (Whole Class)", 
        "🚪 Exit Tickets (Detailed)", 
        "🙋 Hands Up (Volunteers)", 
        "🎯 Cold Call (Interactive Probing)"
    ], horizontal=True, label_visibility="collapsed")
    
    st.markdown("---")
    
    if not teacher_question:
        st.info("👆 Please type an opening question above to begin.")
        return

    # --- MODE: MINI-WHITEBOARDS ---
    if mode == "📝 Mini-Whiteboards (Whole Class)":
        st.caption("Scans the whole room for quick, short-form answers.")
        if st.button("Show All Mini-Whiteboards", type="primary"):
            with st.spinner("Students are writing..."):
                instructions = "Generate a realistic, short answer (maximum 6 words) for EACH student. Focus heavily on quick misconceptions."
                answers = fetch_ai_answers(teacher_question, df, instructions, uploaded_file, cohort, subject)
                
                if answers:
                    num_cols = 5
                    for i in range(0, len(df), num_cols):
                        cols = st.columns(num_cols)
                        for col, (_, row) in zip(cols, df.iloc[i : i + num_cols].iterrows()):
                            with col:
                                name = row.get("Full Name")
                                display_student_photo(name, cohort)
                                st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 13px; margin: 4px 0;'>{name}</div>", unsafe_allow_html=True)
                                ans = answers.get(name, "?")
                                st.markdown(f"<div style='background-color: #ffffff; border: 3px solid #2C3E50; border-radius: 6px; padding: 10px 5px; margin-bottom: 20px; min-height: 70px; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'><span style='color: #1a1a1a; font-size: 14px; font-weight: bold; text-align: center;'>{ans}</span></div>", unsafe_allow_html=True)

    # --- MODE: EXIT TICKETS ---
    elif mode == "🚪 Exit Tickets (Detailed)":
        st.caption("Collects a detailed paragraph from a 'Targeted Marking Pile' of 8 students.")
        if st.button("Collect Exit Tickets", type="primary"):
            with st.spinner("Students are writing..."):
                target_df = df.sample(n=min(8, len(df))) 
                instructions = "Generate a detailed, full-sentence explanation (2 to 4 sentences) for EACH student. Include bracketed visual formatting descriptions."
                answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file, cohort, subject)
                
                if answers: 
                    for _, row in target_df.iterrows():
                        name = row.get("Full Name")
                        ans = answers.get(name, "No ticket submitted.")
                        with st.expander(f"🎫 {name}'s Ticket"):
                            col1, col2 = st.columns([1, 5])
                            with col1: display_student_photo(name, cohort)
                            with col2: st.write(ans)

    # --- MODE: HANDS UP ---
    elif mode == "🙋 Hands Up (Volunteers)":
        st.caption("Simulates 5 students volunteering to answer the question.")
        if st.button("See who raised their hand...", type="primary"):
            with st.spinner("Looking around..."):
                volunteers_df = df.sample(n=min(5, len(df)))
                instructions = "Generate a spoken answer for EACH student. They volunteered, so they feel confident, but may share a confident misconception."
                answers = fetch_ai_answers(teacher_question, volunteers_df, instructions, uploaded_file, cohort, subject)
                
                if answers:
                    for _, row in volunteers_df.iterrows():
                        name = row.get("Full Name")
                        ans = answers.get(name, "...")
                        st.markdown(f"<div style='background-color: #f8f9fa; border-left: 5px solid #f1c40f; padding: 15px; margin-bottom: 10px; border-radius: 4px;'><strong>{name} raises their hand:</strong> \"{ans}\"</div>", unsafe_allow_html=True)

    # --- MODE: COLD CALL (INTERACTIVE PROBING) ---
    elif mode == "🎯 Cold Call (Interactive Probing)":
        st.caption("Put a student on the spot, listen to their answer, and ask follow-up questions to probe their understanding.")
        target_name = st.selectbox("Select student to Cold Call:", df["Full Name"].tolist())
        
        chat_key = f"probe_chat_{target_name}"
        
        # Initialize chat history if it doesn't exist
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
            
        col1, col2 = st.columns([1, 4])
        with col1:
            display_student_photo(target_name, cohort)
            if st.button("🔄 Reset Chat", use_container_width=True):
                st.session_state[chat_key] = []
                st.rerun()
                
        with col2:
            # 1. THE OPENING QUESTION
            if len(st.session_state[chat_key]) == 0:
                if st.button(f"🗣️ Ask {target_name} the opening question", type="primary"):
                    with st.spinner(f"Waiting for {target_name} to respond..."):
                        target_df = df[df["Full Name"] == target_name]
                        instructions = "Generate a spoken answer for this specific student based on their profile. Include hesitation or filler words ('Umm') if appropriate."
                        
                        # We use the batch function just for convenience, grabbing the single dictionary result
                        answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file, cohort, subject)
                        
                        if answers:
                            student_reply = answers.get(target_name, "...")
                            # Save the interaction to memory
                            st.session_state[chat_key].append({"role": "teacher", "content": teacher_question})
                            st.session_state[chat_key].append({"role": "student", "content": student_reply})
                            st.rerun()
                            
            # 2. THE PROBING CONVERSATION
            else:
                # Render the chat history
                for msg in st.session_state[chat_key]:
                    if msg["role"] == "teacher":
                        with st.chat_message("user"): st.write(msg["content"])
                    else:
                        with st.chat_message("assistant"): st.write(msg["content"])
                        
                # 3. THE FOLLOW-UP INPUT
                follow_up = st.chat_input(f"Probe {target_name} deeper...")
                if follow_up:
                    st.session_state[chat_key].append({"role": "teacher", "content": follow_up})
                    with st.chat_message("user"): st.write(follow_up)
                    
                    with st.spinner(f"{target_name} is thinking..."):
                        # We build a custom plain-text prompt for the ongoing chat so it remembers the context
                        target_row = df[df["Full Name"] == target_name].iloc[0]
                        target_grade = get_flexible_text(target_row, ["Projected Grade", "Predicted Grade"])
                        target_sen = get_flexible_text(target_row, ["SEN Status", "SEND Status"])
                        
                        # Build the transcript so the AI knows what has been said
                        transcript = "\n".join([f"{'Teacher' if m['role']=='teacher' else 'Student'}: {m['content']}" for m in st.session_state[chat_key]])
                        
                        chat_prompt = f"""
                        You are roleplaying as {target_name}, a {cohort} student. Target Grade: {target_grade}, SEN: {target_sen}.
                        The subject is {subject}. 
                        
                        Here is the conversation so far:
                        {transcript}
                        
                        Respond to the teacher's last question as {target_name}. Keep it brief (1-2 sentences). 
                        If the teacher has successfully guided you to the right answer, show realization. If their hint was confusing, stay confused.
                        """
                        
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        try:
                            reply = model.generate_content(chat_prompt)
                            st.session_state[chat_key].append({"role": "student", "content": reply.text})
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to generate response. You may have hit the speed limit.")
