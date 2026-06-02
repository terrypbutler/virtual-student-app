import streamlit as st
import google.generativeai as genai
import json
import time
from PIL import Image
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
    return "Unknown"

def fetch_ai_answers(question, student_subset, instructions, uploaded_file, cohort, subject):
    """Centralized function to call Gemini with the Advanced Pedagogical Mega-Prompt."""
    
    age_context = "11 to 12 years old" if cohort == "Year 7" else "14 to 15 years old"
    
    # 1. Build the ultra-rich profile list
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
        
        profiles.append(f"- {name} | Target: {grade} | SEN: {sen} | EAL: {eal} | KS2 Math: {math_score} | KS2 Read: {read_score} | Suspensions: {suspensions} | Home Context: {home_life}")
        
    profiles_text = "\n".join(profiles)
    
    # 2. The Master Prompt
    prompt = f"""
    A trainee teacher is conducting a {subject} lesson for a class of {cohort} students (approximate age: {age_context}).
    The teacher has asked the class: "{question}"
    
    First, internally assess the cognitive demand and age-appropriateness of this question. If the trainee is asking a university-level question to 11-year-olds, the students should express intense confusion or give wildly inaccurate guesses.
    
    Here is the detailed data for the specific students answering:
    {profiles_text}
    
    {instructions}
    
    CRITICAL PEDAGOGICAL CONSTRAINTS FOR YOUR GENERATION:
    1. Ability Match: You MUST scale the vocabulary, accuracy, and depth of the answer to match their Target Grade and KS2/SATs scores. 
    2. Deep Misconceptions: This is a training simulator. For students with lower grades or SEN, you MUST heavily inject realistic, {subject}-specific misconceptions, procedural errors, partial misunderstandings, or phonetic spelling mistakes. Do not just make them say "I don't know." Give them a wrong answer that makes logical sense to a struggling teenager.
    3. Attitude & Randomness: Factor in their suspension data and home context. Randomly assign a "mood" (great day vs. bad day) to each student. A high-achiever having a bad day might give a lazy, clipped answer. A struggling student having a great day might try really hard but still get it wrong. Students with high suspensions might give defiant or off-topic answers.
    4. Visual Presentation: If the instructions ask for a detailed or long answer (like an Exit Ticket), prepend the text with a bracketed description of how the work looks visually (e.g., [Heavily crossed out with doodles in the margin], [Immaculate bullet points], [Written entirely in capital letters]).
    
    CRITICAL TECHNICAL RULES:
    - If the answer requires mathematics, format it simply using standard keyboard symbols (like x^2) or Unicode (like x²). Do not use complex LaTeX.
    - Return ONLY a valid JSON dictionary where the keys are the exact student names and the values are their answers. Do not include any other text.
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            contents = [prompt]
            if uploaded_file is not None:
                contents.append(Image.open(uploaded_file))
                
            response = model.generate_content(
                contents, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
            
        except Exception as e:
            error_msg = str(e)
            if "ResourceExhausted" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    st.toast(f"🚦 AI Speed Limit hit. Auto-retrying in 20 seconds... (Attempt {attempt + 1} of {max_retries})")
                    time.sleep(20)
                else:
                    st.error("🚦 The AI is completely exhausted. Please wait a full 60 seconds before asking another question.")
                    return {}
            else:
                st.error("Failed to fetch AI response. Please check your question and try again.")
                return {}

def render_academic_responses(df, cohort, subject="General"):
    st.subheader(f"🎓 AfL Simulator: {subject} Questioning")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing.")
        return
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # --- 1. THE INPUT AREA ---
    st.markdown("### 1. Present the Material")
    teacher_question = st.text_area("Ask the class a question:")
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
        "🎯 Cold Call (Targeted)"
    ], horizontal=True, label_visibility="collapsed")
    
    st.markdown("---")
    
    if not teacher_question:
        st.info("👆 Please type a question above to begin.")
        return

    # --- MODE: MINI-WHITEBOARDS ---
    if mode == "📝 Mini-Whiteboards (Whole Class)":
        st.caption("Scans the whole room for quick, short-form answers.")
        if st.button("Show All Mini-Whiteboards", type="primary"):
            with st.spinner("Students are writing..."):
                instructions = "Generate a realistic, short answer (maximum 6 words) for EACH student. Focus heavily on quick misconceptions."
                answers = fetch_ai_answers(teacher_question, df, instructions, uploaded_file, cohort, subject)
                
                if answers:
                    st.markdown("### Classroom Whiteboards")
                    num_cols = 5
                    for i in range(0, len(df), num_cols):
                        cols = st.columns(num_cols)
                        for col, (_, row) in zip(cols, df.iloc[i : i + num_cols].iterrows()):
                            with col:
                                name = row.get("Full Name")
                                display_student_photo(name, cohort)
                                st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 13px; margin: 4px 0;'>{name}</div>", unsafe_allow_html=True)
                                
                                ans = answers.get(name, "?")
                                st.markdown(f"""
                                    <div style='background-color: #ffffff; border: 3px solid #2C3E50; border-radius: 6px; 
                                                padding: 10px 5px; margin-bottom: 20px; min-height: 70px; display: flex; 
                                                align-items: center; justify-content: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>
                                        <span style='color: #1a1a1a; font-size: 14px; font-weight: bold; text-align: center;'>{ans}</span>
                                    </div>
                                """, unsafe_allow_html=True)

    # --- MODE: EXIT TICKETS ---
    elif mode == "🚪 Exit Tickets (Detailed)":
        st.caption("Collects a detailed paragraph from a 'Targeted Marking Pile' of 8 students to check deep understanding.")
        if st.button("Collect Exit Tickets", type="primary"):
            with st.spinner("Students are writing their paragraphs..."):
                target_df = df.sample(n=min(8, len(df))) 
                instructions = "Generate a detailed, full-sentence explanation (2 to 4 sentences) for EACH student. You MUST include the bracketed visual formatting description at the start of every response."
                answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file, cohort, subject)
                
                if answers: 
                    st.markdown(f"### 📑 Teacher's Marking Pile ({len(target_df)} selected at random)")
                    for _, row in target_df.iterrows():
                        name = row.get("Full Name")
                        ans = answers.get(name, "No ticket submitted.")
                        with st.expander(f"🎫 {name}'s Ticket"):
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                display_student_photo(name, cohort)
                            with col2:
                                st.write(ans)

    # --- MODE: HANDS UP ---
    elif mode == "🙋 Hands Up (Volunteers)":
        st.caption("Simulates 5 students volunteering to answer the question.")
        if st.button("See who raised their hand...", type="primary"):
            with st.spinner("Looking around the room..."):
                volunteers_df = df.sample(n=min(5, len(df)))
                instructions = "Generate a spoken, conversational answer for EACH of these volunteering students. Since they volunteered, they feel confident, but they may confidently share a complete misconception."
                answers = fetch_ai_answers(teacher_question, volunteers_df, instructions, uploaded_file, cohort, subject)
                
                if answers:
                    st.markdown("### 🖐️ Volunteers")
                    for _, row in volunteers_df.iterrows():
                        name = row.get("Full Name")
                        ans = answers.get(name, "...")
                        
                        st.markdown(f"""
                            <div style='background-color: #f8f9fa; border-left: 5px solid #f1c40f; padding: 15px; margin-bottom: 10px; border-radius: 4px;'>
                                <strong>{name} raises their hand:</strong> "{ans}"
                            </div>
                        """, unsafe_allow_html=True)

    # --- MODE: COLD Call ---
    elif mode == "🎯 Cold Call (Targeted)":
        st.caption("Select a specific student and put them on the spot.")
        target_name = st.selectbox("Select student to Cold Call:", df["Full Name"].tolist())
        
        if st.button(f"Ask {target_name}", type="primary"):
            with st.spinner(f"Waiting for {target_name} to answer..."):
                target_df = df[df["Full Name"] == target_name]
                instructions = "Generate a spoken, conversational answer for this specific student. Because they were cold-called, they might hesitate, use filler words ('Umm'), or panic slightly depending on their confidence, mood, and ability."
                answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file, cohort, subject)
                
                if answers:
                    ans = answers.get(target_name, "...")
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        display_student_photo(target_name, cohort)
                    with col2:
                        st.markdown(f"""
                            <div style='background-color: #e8f4f8; border: 1px solid #bce8f1; padding: 20px; border-radius: 8px; font-size: 16px;'>
                                🗣️ <strong>{target_name}:</strong> "{ans}"
                            </div>
                        """, unsafe_allow_html=True)
