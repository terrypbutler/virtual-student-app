import streamlit as st
import google.generativeai as genai
import azure.cognitiveservices.speech as speechsdk
import json
import time
import random
import re
from PIL import Image
from modules.photo_utils import display_student_photo

# --- OFFICIAL AZURE TTS ENGINE ---
def get_azure_audio(text, voice_name="en-GB-RyanNeural", pitch="+0%", rate="+0%"):
    """Generates audio using the official Azure SDK with SSML for pitch/rate control."""
    if "AZURE_SPEECH_KEY" not in st.secrets or "AZURE_SPEECH_REGION" not in st.secrets:
        st.error("⚠️ Azure Speech Key or Region missing in secrets.toml.")
        return None

    if not voice_name or str(voice_name).upper() in ["NAN", "NONE", "", "N/A"]:
        voice_name = "en-GB-RyanNeural"

    # Set up the Azure configuration
    speech_config = speechsdk.SpeechConfig(
        subscription=st.secrets["AZURE_SPEECH_KEY"], 
        region=st.secrets["AZURE_SPEECH_REGION"]
    )
    
    # We want to get the audio bytes back, not play it directly on the server speaker
    audio_config = speechsdk.audio.PullAudioOutputStream()
    stream_config = speechsdk.audio.AudioOutputConfig(stream=audio_config)
    
    # Ensure audio format is standard for web players (e.g., MP3 or WAV)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=stream_config)

    # Convert generic pitch (e.g., "+10Hz" or "+10%") to SSML percentage format
    # Azure SSML prefers relative percentages for pitch
    clean_pitch = pitch.replace("Hz", "%") 
    
    # Build the SSML (Speech Synthesis Markup Language) string
    ssml_string = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-GB">
        <voice name="{voice_name}">
            <prosody pitch="{clean_pitch}" rate="{rate}">
                {text}
            </prosody>
        </voice>
    </speak>
    """

    try:
        # Generate the audio
        result = synthesizer.speak_ssml_async(ssml_string).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            st.error(f"Azure Speech Cancelled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                st.error(f"Azure Error Details: {cancellation_details.error_details}")
            return None
    except Exception as e:
        st.error(f"Failed to fetch Azure audio: {e}")
        return None

def get_flexible_text(row, possible_names, default="None recorded"):
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                if val.endswith(".0"): val = val[:-2]
                return val
    return default

def calculate_emotion_modifiers(base_pitch, base_rate, emotion):
    """Dynamically alters the voice based on the AI-determined mood."""
    try: bp_val = int(base_pitch.replace("Hz", "").replace("%", "").replace("+", ""))
    except: bp_val = 0
    try: br_val = int(base_rate.replace("%", "").replace("+", ""))
    except: br_val = 0
    
    if emotion == "angry" or emotion == "defensive":
        br_val += 15 
        bp_val -= 5   
    elif emotion == "sad" or emotion == "bored" or emotion == "hesitant":
        br_val -= 20  
        bp_val -= 10  
    elif emotion == "excited" or emotion == "eager":
        br_val += 10  
        bp_val += 15  
        
    final_pitch = f"+{bp_val}%" if bp_val >= 0 else f"{bp_val}%"
    final_rate = f"+{br_val}%" if br_val >= 0 else f"{br_val}%"
    
    return final_pitch, final_rate

def fetch_ai_answers(question, student_subset, instructions, uploaded_file, cohort, subject, teacher_name, is_written=False):
    age_context = "11 to 12 years old" if cohort == "Year 7" else "14 to 15 years old"
    
    profiles = []
    for _, row in student_subset.iterrows():
        name = row.get("Full Name")
        grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
        sen = get_flexible_text(row, ["SEN Status", "SEND Status"])
        eal = get_flexible_text(row, ["EAL", "EAL Status"])
        math_score = get_flexible_text(row, ["KS2 Maths", "KS2 Math", "SATs Maths"])
        read_score = get_flexible_text(row, ["KS2 Read", "KS2 Reading", "SATs Reading"])
        susp = get_flexible_text(row, ["Suspension days", "Suspensions"])
        home = get_flexible_text(row, ["Home Life & Interests", "Home Life"])
        profiles.append(f"- {name} | Target: {grade} | SEN: {sen} | EAL: {eal} | KS2 Math: {math_score} | KS2 Read: {read_score} | Susp: {susp} | Home: {home}")
        
    profiles_text = "\n".join(profiles)
    
    if is_written:
        address_rule = "4. Written Work: DO NOT use the teacher's name or titles like 'Sir' or 'Miss' in the response. It must read entirely like an exercise book or whiteboard."
    else:
        address_rule = f"4. Teacher Address: The students should occasionally use the teacher's name/title ('{teacher_name}') naturally in their verbal responses (e.g., 'I think it's 4, {teacher_name}')."
    
    prompt = f"""
    A trainee teacher (addressed as '{teacher_name}') is conducting a {subject} lesson for a class of {cohort} students (approximate age: {age_context}).
    The teacher has asked the class: "{question}"
    
    Here is the detailed data for the specific students answering:
    {profiles_text}
    
    {instructions}
    
    CRITICAL PEDAGOGICAL CONSTRAINTS:
    1. Ability Match: Scale vocabulary, accuracy, length, and depth to their Target Grade and KS2/SATs scores. 
    2. Deep Misconceptions: Inject realistic, {subject}-specific misconceptions or partial misunderstandings for lower grades.
    3. Attitude: Factor in suspensions and home context to randomly assign a mood.
    {address_rule}
    5. Math Formatting: Make maths look like real maths. DO NOT use raw carets (like r^2). You MUST use Unicode superscripts (e.g., r², x³, y₁) and symbols (π, √, ÷, ×, ±). For complex equations, use LaTeX wrapped in single `$` (e.g., `$x = \\frac{{1}}{{2}}$`).
    6. Layout: If the answer involves multiple steps of calculation, you MUST put each step on a new line using a newline character (\\n).
    
    CRITICAL TECHNICAL RULES:
    - Return ONLY a valid JSON dictionary where keys are exact student names and values are their answers.
    - If you use LaTeX, you MUST double-escape the backslashes (e.g., `\\\\frac`, `\\\\sqrt`) so the JSON parser does not crash.
    """
    
    for attempt in range(3):
        try:
            model = genai.GenerativeModel('gemini-2.5-pro')
            contents = [prompt]
            if uploaded_file is not None: contents.append(Image.open(uploaded_file))
                
            response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
            
            raw_text = response.text
            raw_text = raw_text.replace("`" * 3 + "json", "")
            raw_text = raw_text.replace("`" * 3, "")
            return json.loads(raw_text.strip())
            
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                st.toast(f"🚦 AI Speed Limit hit. Auto-retrying in 20 seconds...")
                time.sleep(20)
            elif attempt == 2:
                st.error("🚦 AI exhausted. Please wait 60 seconds.")
                return {}
    return {}

def create_printable_worksheet(question, answers, df, subject, cohort):
    html = [
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Marking Practice</title>",
        "<script src='https://polyfill.io/v3/polyfill.min.js?features=es6'></script>",
        "<script id='MathJax-script' async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script>",
        "<style>",
        "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #222; line-height: 1.5; }",
        "@media print { body { margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; } .student-box { page-break-inside: avoid; } }",
        ".header { text-align: center; border-bottom: 2px solid #2C3E50; padding-bottom: 10px; margin-bottom: 20px; }",
        ".reflection-box { background: #e8f4f8; border: 2px solid #3498DB; padding: 20px; margin-bottom: 30px; border-radius: 8px; }",
        ".reflection-box h3 { margin-top: 0; color: #2C3E50; font-size: 18px; }",
        ".reflection-box ul { margin: 0; padding-left: 20px; font-weight: bold; color: #333; font-size: 15px; }",
        ".reflection-box li { margin-bottom: 6px; }",
        ".question-box { background: #f8f9fa; padding: 15px; border-left: 5px solid #E67E22; margin-bottom: 30px; font-size: 16px; }",
        ".student-box { border: 2px solid #ddd; padding: 20px; margin-bottom: 25px; border-radius: 8px; }",
        ".student-name { font-size: 18px; font-weight: bold; color: #2C3E50; margin-bottom: 4px; }",
        ".student-profile { font-size: 12px; color: #666; margin-bottom: 12px; background: #eee; display: inline-block; padding: 3px 8px; border-radius: 4px; }",
        ".student-answer { font-size: 15px; margin-bottom: 30px; line-height: 1.6; font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif; color: #000080; }",
        "del { color: #d9534f; text-decoration: line-through; }", 
        ".marking-area { border-top: 2px dashed #ccc; padding-top: 15px; min-height: 120px; }",
        ".marking-title { font-weight: bold; font-size: 14px; color: #E67E22; text-transform: uppercase; letter-spacing: 1px; }",
        "</style></head><body>",
        f"<div class='header'><h2>ITT Marking Practice: {cohort} {subject}</h2></div>",
        "<div class='reflection-box'>",
        "<h3>Trainee Reflection Prompts:</h3>",
        "<ul>",
        "<li>Who understands the problem but still loses marks?</li>",
        "<li>Who doesn’t finish — and why?</li>",
        "<li>Which responses would collapse under exam conditions?</li>",
        "<li>If this was your class, what would you do now?</li>",
        "<li>Who needs scaffolding not stretch?</li>",
        "<li>Who needs slowing down not challenge?</li>",
        "<li>Who needs feedback on presentation, not maths?</li>",
        "</ul>",
        "</div>",
        f"<div class='question-box'><strong>Teacher's Prompt / Exit Ticket Question:</strong><br><br>{question}</div>"
    ]

    for _, row in df.iterrows():
        name = row.get("Full Name", "Unknown")
        grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
        sen = get_flexible_text(row, ["SEN Status", "SEND Status"])
        
        raw_ans = answers.get(name, "No response submitted.")
        
        html_ans = re.sub(r'~~(.*?)~~', r'<del>\1</del>', str(raw_ans))
        html_ans = html_ans.replace("\n", "<br>")

        profile_text = f"Target: {grade}"
        if sen and sen.upper() not in ["N/A", "NONE", "NO", "N", ""]:
            profile_text += f" | SEN: {sen}"

        html.append(f"<div class='student-box'>")
        html.append(f"<div class='student-name'>{name}</div>")
        html.append(f"<div class='student-profile'>Context for Trainee: {profile_text}</div>")
        html.append(f"<div class='student-answer'>{html_ans}</div>")
        html.append(f"<div class='marking-area'><span class='marking-title'>Trainee Feedback / Next Steps:</span></div>")
        html.append(f"</div>")

    html.append("</body></html>")
    return "\n".join(html)

def render_academic_responses(df, cohort, subject="General"):
    st.subheader(f"🎓 AfL Simulator: {subject} Questioning")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing.")
        return
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    if "wb_answers" not in st.session_state: st.session_state.wb_answers = None
    if "wb_probe_selected" not in st.session_state: st.session_state.wb_probe_selected = None

    # --- 1. THE INPUT AREA ---
    st.markdown("### 1. Present the Material")
    teacher_name = st.text_input("Your Title/Name (e.g., Mr. Smith, Miss, Sir):", value="Sir")
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
        st.caption("Scans the whole room for quick, short-form answers. Click 'Probe' under a student to question their specific answer.")
        
        if st.session_state.wb_probe_selected:
            target_name = st.session_state.wb_probe_selected
            st.markdown(f"### 🗣️ Probing {target_name}'s Whiteboard Answer")
            
            chat_key = f"probe_chat_{target_name}"
            
            col_a, col_b = st.columns([1, 4])
            with col_a:
                display_student_photo(target_name, cohort)
                
                raw_ans = st.session_state.wb_answers.get(target_name, "?")
                md_ans = str(raw_ans).replace("\n", "\n\n")
                
                with st.container(border=True):
                    st.markdown(f"<div style='text-align: center; font-size: 1.4rem; padding: 15px 0;'>\n\n{md_ans}\n\n</div>", unsafe_allow_html=True)
                
                if st.button("🔙 Back to Whiteboards", use_container_width=True):
                    st.session_state.wb_probe_selected = None
                    st.rerun()
                    
            with col_b:
                if "latest_audio" in st.session_state:
                    st.audio(st.session_state["latest_audio"], format="audio/mp3", autoplay=True)
                    del st.session_state["latest_audio"]
                    
                for msg in st.session_state[chat_key]:
                    msg_text = str(msg["content"]).replace("\n", "\n\n")
                    if msg["role"] == "teacher":
                        with st.chat_message("user"): st.markdown(msg_text)
                    else:
                        with st.chat_message("assistant"): st.markdown(msg_text)
                        
                follow_up = st.chat_input(f"Ask {target_name} about their whiteboard answer...")
                if follow_up:
                    st.session_state[chat_key].append({"role": "teacher", "content": follow_up})
                    with st.chat_message("user"): st.markdown(follow_up)
                    
                    with st.spinner(f"{target_name} is reacting..."):
                        target_row = df[df["Full Name"] == target_name].iloc[0]
                        target_grade = get_flexible_text(target_row, ["Projected Grade", "Predicted Grade"])
                        target_sen = get_flexible_text(target_row, ["SEN Status", "SEND Status"])
                        
                        student_voice_name = target_row.get("Voice_Name", "en-GB-RyanNeural")
                        base_pitch = get_flexible_text(target_row, ["Base_Pitch", "Pitch"], default="+0%")
                        base_rate = get_flexible_text(target_row, ["Base_Rate", "Rate"], default="+0%")
                        
                        transcript = "\n".join([f"{'Teacher' if m['role']=='teacher' else 'Student'}: {m['content']}" for m in st.session_state[chat_key]])
                        
                        chat_prompt = f"""
                        You are roleplaying as {target_name}, a {cohort} student. Target Grade: {target_grade}, SEN: {target_sen}.
                        The subject is {subject}. The teacher's name/title is {teacher_name}.
                        
                        Here is the conversation so far. Note that your first response was a written answer on a mini-whiteboard:
                        {transcript}
                        
                        CRITICAL RULES:
                        1. Respond verbally to the teacher's last question as {target_name}. Keep it brief. 
                        2. Determine the student's current emotion based on the scenario and teacher's prompt. Pick ONE: [neutral, angry, defensive, sad, bored, hesitant, excited, eager].
                        3. You MUST return your response as a raw JSON object with two keys: "dialogue" and "emotion".
                        
                        Example Format:
                        {{"dialogue": "I think it's 4, {teacher_name}", "emotion": "hesitant"}}
                        """
                        
                        try:
                            model = genai.GenerativeModel('gemini-2.5-pro')
                            response = model.generate_content(chat_prompt, generation_config={"response_mime_type": "application/json"})
                            
                            ai_data = json.loads(response.text)
                            reply_text = ai_data.get("dialogue", "...")
                            current_emotion = ai_data.get("emotion", "neutral")
                            
                            st.session_state[chat_key].append({"role": "student", "content": reply_text})
                            
                            active_pitch, active_rate = calculate_emotion_modifiers(base_pitch, base_rate, current_emotion)
                            st.toast(f"Student Mood: {current_emotion.upper()} 🎭")
                            
                            audio_bytes = get_azure_audio(reply_text, student_voice_name, pitch=active_pitch, rate=active_rate)
                            if audio_bytes:
                                st.session_state["latest_audio"] = audio_bytes
                            st.rerun()
                                
                        except Exception as e:
                            st.error(f"Failed to generate response: {e}")
                            
        else:
            if st.session_state.wb_answers is None:
                if st.button("Show All Mini-Whiteboards", type="primary"):
                    with st.spinner("Students are scribbling on their boards..."):
                        instructions = "Write ONLY the absolute minimum factual or mathematical answer the student would scribble on a whiteboard (1 to 4 words max). Do not write full sentences. Do not include commentary. Be extremely brief. CRITICAL: Inject realistic, age-appropriate spelling and grammar mistakes, particularly for students with lower target grades, SEN, or EAL status."
                        answers = fetch_ai_answers(teacher_question, df, instructions, uploaded_file, cohort, subject, teacher_name, is_written=True)
                        
                    if answers:
                        reveal_text = st.empty()
                        for word in ["Three...", "Two...", "One...", "Show me!"]:
                            reveal_text.markdown(f"<h2 style='text-align: center; color: #E67E22;'>{word}</h2>", unsafe_allow_html=True)
                            time.sleep(0.7)
                        reveal_text.empty() 
                        
                        st.session_state.wb_answers = answers
                        st.rerun()
            else:
                if st.button("🔄 Clear Whiteboards", type="secondary"):
                    st.session_state.wb_answers = None
                    st.rerun()
                    
                st.markdown("---")
                num_cols = 5
                for i in range(0, len(df), num_cols):
                    cols = st.columns(num_cols)
                    for col, (_, row) in zip(cols, df.iloc[i : i + num_cols].iterrows()):
                        with col:
                            name = row.get("Full Name")
                            display_student_photo(name, cohort)
                            st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 13px; margin: 4px 0;'>{name}</div>", unsafe_allow_html=True)
                            
                            raw_ans = st.session_state.wb_answers.get(name, "?")
                            md_ans = str(raw_ans).replace("\n", "\n\n")
                            
                            with st.container(border=True):
                                st.markdown(f"<div style='text-align: center; font-size: 1.4rem; padding: 15px 0;'>\n\n{md_ans}\n\n</div>", unsafe_allow_html=True)
                            
                            if st.button(f"🗣️ Probe", key=f"probe_{name}", use_container_width=True):
                                st.session_state.wb_probe_selected = name
                                chat_key = f"probe_chat_{name}"
                                st.session_state[chat_key] = [
                                    {"role": "teacher", "content": teacher_question},
                                    {"role": "student", "content": f"[Wrote on whiteboard]: {raw_ans}"}
                                ]
                                st.rerun()

    # --- MODE: EXIT TICKETS ---
    elif mode == "🚪 Exit Tickets (Detailed)":
        st.caption("Collects a detailed paragraph from every single student in the class.")
        if st.button("Collect Exit Tickets", type="primary"):
            with st.spinner("Students are writing their work (this may take a moment for a full class on the Pro model)..."):
                
                instructions = (
                    "Write EXACTLY what the student would write in their exercise book. "
                    "CRITICAL REALISM BY TARGET GRADE: You MUST scale the actual quality of the English, sentence structure, and vocabulary to their specific Target Grade.\n"
                    "- Target Grade 7-9: Flawless or near-perfect grammar. Highly articulate, structured, and fluent. No forced errors.\n"
                    "- Target Grade 4-6: Typical teenager. Mostly accurate, but might lack depth, use casual phrasing, or have occasional minor punctuation slips.\n"
                    "- Target Grade 1-3: Noticeably weak literacy. Use very basic vocabulary, short fragmented sentences, and struggle to articulate the 'why'. They should sound like a student with a low reading age. Inject realistic spelling errors (phonetic spelling of hard words) and crossed-out mistakes using Markdown strikethrough (~~like this~~).\n"
                    "DO NOT include any AI commentary or explanation. Output raw student work only."
                )
                
                answers = fetch_ai_answers(teacher_question, df, instructions, uploaded_file, cohort, subject, teacher_name, is_written=True)
                
                if answers: 
                    st.success("✅ All exit tickets collected!")
                    html_worksheet = create_printable_worksheet(teacher_question, answers, df, subject, cohort)
                    st.download_button(
                        label="🖨️ Download as Printable Worksheet",
                        data=html_worksheet,
                        file_name=f"{cohort}_{subject}_Full_Class_Marking_Exercise.html",
                        mime="text/html",
                        help="Downloads a perfectly formatted file. Open it in your browser and press Ctrl+P to print!",
                        type="secondary",
                        use_container_width=True
                    )
                    st.markdown("---")
                    st.markdown(f"### 📑 On-Screen Preview (Full Class)")
                    for _, row in df.iterrows():
                        name = row.get("Full Name")
                        raw_ans = answers.get(name, "No ticket submitted.")
                        st_ans = str(raw_ans).replace("\n", "\n\n")
                        
                        with st.expander(f"🎫 {name}'s Ticket"):
                            col1, col2 = st.columns([1, 5])
                            with col1: display_student_photo(name, cohort)
                            with col2: st.markdown(st_ans)

    # --- MODE: HANDS UP ---
    elif mode == "🙋 Hands Up (Volunteers)":
        st.caption("A random number of students will volunteer. Select one to hear their answer and probe deeper.")
        
        if "hu_volunteers" not in st.session_state: st.session_state.hu_volunteers = []
        if "hu_selected" not in st.session_state: st.session_state.hu_selected = None

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🙋 Ask for Volunteers", type="primary", use_container_width=True):
                num_vols = random.randint(3, min(10, len(df)))
                vol_df = df.sample(n=num_vols)
                st.session_state.hu_volunteers = vol_df["Full Name"].tolist()
                st.session_state.hu_selected = None
                st.rerun()
            if st.button("🔄 Clear Hands", use_container_width=True):
                st.session_state.hu_volunteers = []
                st.session_state.hu_selected = None
                st.rerun()

        st.markdown("---")

        if st.session_state.hu_volunteers and not st.session_state.hu_selected:
            st.markdown("### 🖐️ Look who raised their hand:")
            vols = st.session_state.hu_volunteers
            
            for i in range(0, len(vols), 5):
                cols = st.columns(5)
                for idx, vol_name in enumerate(vols[i : i + 5]):
                    with cols[idx]:
                        display_student_photo(vol_name, cohort)
                        if st.button(f"Call on {vol_name}", key=f"btn_{vol_name}", use_container_width=True):
                            st.session_state.hu_selected = vol_name
                            st.rerun()

        elif st.session_state.hu_selected:
            target_name = st.session_state.hu_selected
            st.markdown(f"### 🗣️ You called on {target_name}")

            chat_key = f"probe_chat_{target_name}"
            if chat_key not in st.session_state: st.session_state[chat_key] = []

            col_a, col_b = st.columns([1, 4])
            with col_a:
                display_student_photo(target_name, cohort)
                if st.button("🔄 Pick Someone Else", use_container_width=True):
                    st.session_state.hu_selected = None
                    st.rerun()

            with col_b:
                if "latest_audio" in st.session_state:
                    st.audio(st.session_state["latest_audio"], format="audio/mp3", autoplay=True)
                    del st.session_state["latest_audio"]
                    
                if len(st.session_state[chat_key]) == 0:
                    with st.spinner(f"Waiting for {target_name} to respond..."):
                        target_df = df[df["Full Name"] == target_name]
                        instructions = "Generate a spoken answer. They volunteered, so they feel confident, but may confidently share a misconception. No commentary."
                        answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file, cohort, subject, teacher_name)

                        if answers:
                            student_reply = answers.get(target_name, "...")
                            st.session_state[chat_key].append({"role": "teacher", "content": teacher_question})
                            st.session_state[chat_key].append({"role": "student", "content": student_reply})
                            
                            target_row = df[df["Full Name"] == target_name].iloc[0]
                            student_voice_name = target_row.get("Voice_Name", "en-GB-RyanNeural")
                            base_pitch = get_flexible_text(target_row, ["Base_Pitch", "Pitch"], default="+0%")
                            base_rate = get_flexible_text(target_row, ["Base_Rate", "Rate"], default="+0%")
                            
                            audio_bytes = get_azure_audio(student_reply, student_voice_name, pitch=base_pitch, rate=base_rate)
                            if audio_bytes:
                                st.session_state["latest_audio"] = audio_bytes
                            st.rerun()
                else:
                    for msg in st.session_state[chat_key]:
                        msg_text = str(msg["content"]).replace("\n", "\n\n")
                        if msg["role"] == "teacher":
                            with st.chat_message("user"): st.markdown(msg_text)
                        else:
                            with st.chat_message("assistant"): st.markdown(msg_text)

                    follow_up = st.chat_input(f"Probe {target_name} deeper...")
                    if follow_up:
                        st.session_state[chat_key].append({"role": "teacher", "content": follow_up})
                        with st.chat_message("user"): st.markdown(follow_up)
                        
                        with st.spinner(f"{target_name} is reacting..."):
                            target_row = df[df["Full Name"] == target_name].iloc[0]
                            target_grade = get_flexible_text(target_row, ["Projected Grade", "Predicted Grade"])
                            target_sen = get_flexible_text(target_row, ["SEN Status", "SEND Status"])
                            
                            student_voice_name = target_row.get("Voice_Name", "en-GB-RyanNeural")
                            base_pitch = get_flexible_text(target_row, ["Base_Pitch", "Pitch"], default="+0%")
                            base_rate = get_flexible_text(target_row, ["Base_Rate", "Rate"], default="+0%")
                            
                            transcript = "\n".join([f"{'Teacher' if m['role']=='teacher' else 'Student'}: {m['content']}" for m in st.session_state[chat_key]])

                            chat_prompt = f"""
                            You are roleplaying as {target_name}, a {cohort} student. Target Grade: {target_grade}, SEN: {target_sen}.
                            The subject is {subject}. The teacher's name/title is {teacher_name}.

                            Here is the conversation so far:
                            {transcript}

                            CRITICAL RULES:
                            1. Respond to the teacher's last question as {target_name}. Keep it brief (1-2 sentences). 
                            2. Determine the student's current emotion based on the scenario and teacher's prompt. Pick ONE: [neutral, angry, defensive, sad, bored, hesitant, excited, eager].
                            3. You MUST return your response as a raw JSON object with two keys: "dialogue" and "emotion".
                            
                            Example Format:
                            {{"dialogue": "I think it's 4, {teacher_name}", "emotion": "hesitant"}}
                            """
                            
                            try:
                                model = genai.GenerativeModel('gemini-2.5-pro')
                                response = model.generate_content(chat_prompt, generation_config={"response_mime_type": "application/json"})
                                
                                ai_data = json.loads(response.text)
                                reply_text = ai_data.get("dialogue", "...")
                                current_emotion = ai_data.get("emotion", "neutral")
                                
                                st.session_state[chat_key].append({"role": "student", "content": reply_text})
                                
                                active_pitch, active_rate = calculate_emotion_modifiers(base_pitch, base_rate, current_emotion)
                                st.toast(f"Student Mood: {current_emotion.upper()} 🎭")
                                
                                audio_bytes = get_azure_audio(reply_text, student_voice_name, pitch=active_pitch, rate=active_rate)
                                if audio_bytes is None:
                                    st.stop()
                                else:
                                    st.session_state["latest_audio"] = audio_bytes
                                    st.rerun()
                            except Exception as e:
                                st.error("Failed to generate response.")

    # --- MODE: COLD CALL (INTERACTIVE PROBING) ---
    elif mode == "🎯 Cold Call (Interactive Probing)":
        st.caption("Put a student on the spot, listen to their answer, and ask follow-up questions to probe their understanding.")
        target_name = st.selectbox("Select student to Cold Call:", df["Full Name"].tolist())
        
        chat_key = f"probe_chat_{target_name}"
        if chat_key not in st.session_state: st.session_state[chat_key] = []
            
        col1, col2 = st.columns([1, 4])
        with col1:
            display_student_photo(target_name, cohort)
            if st.button("🔄 Reset Chat", use_container_width=True):
                st.session_state[chat_key] = []
                st.rerun()
                
        with col2:
            if "latest_audio" in st.session_state:
                st.audio(st.session_state["latest_audio"], format="audio/mp3", autoplay=True)
                del st.session_state["latest_audio"]
                
            if len(st.session_state[chat_key]) == 0:
                if st.button(f"🗣️ Ask {target_name} the opening question", type="primary"):
                    with st.spinner(f"Waiting for {target_name} to respond..."):
                        target_df = df[df["Full Name"] == target_name]
                        instructions = "Generate a spoken answer based on their profile. Include hesitation or filler words ('Umm') if appropriate. NO commentary."
                        answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file, cohort, subject, teacher_name)
                        
                        if answers:
                            student_reply = answers.get(target_name, "...")
                            st.session_state[chat_key].append({"role": "teacher", "content": teacher_question})
                            st.session_state[chat_key].append({"role": "student", "content": student_reply})
                            
                            target_row = df[df["Full Name"] == target_name].iloc[0]
                            student_voice_name = target_row.get("Voice_Name", "en-GB-RyanNeural")
                            base_pitch = get_flexible_text(target_row, ["Base_Pitch", "Pitch"], default="+0%")
                            base_rate = get_flexible_text(target_row, ["Base_Rate", "Rate"], default="+0%")
                            
                            audio_bytes = get_azure_audio(student_reply, student_voice_name, pitch=base_pitch, rate=base_rate)
                            if audio_bytes:
                                st.session_state["latest_audio"] = audio_bytes
                            st.rerun()
            else:
                for msg in st.session_state[chat_key]:
                    msg_text = str(msg["content"]).replace("\n", "\n\n")
                    if msg["role"] == "teacher":
                        with st.chat_message("user"): st.markdown(msg_text)
                    else:
                        with st.chat_message("assistant"): st.markdown(msg_text)
                        
                follow_up = st.chat_input(f"Probe {target_name} deeper...")
                if follow_up:
                    st.session_state[chat_key].append({"role": "teacher", "content": follow_up})
                    with st.chat_message("user"): st.markdown(follow_up)
                    
                    with st.spinner(f"{target_name} is reacting..."):
                        target_row = df[df["Full Name"] == target_name].iloc[0]
                        target_grade = get_flexible_text(target_row, ["Projected Grade", "Predicted Grade"])
                        target_sen = get_flexible_text(target_row, ["SEN Status", "SEND Status"])
                        
                        student_voice_name = target_row.get("Voice_Name", "en-GB-RyanNeural")
                        base_pitch = get_flexible_text(target_row, ["Base_Pitch", "Pitch"], default="+0%")
                        base_rate = get_flexible_text(target_row, ["Base_Rate", "Rate"], default="+0%")
                        
                        transcript = "\n".join([f"{'Teacher' if m['role']=='teacher' else 'Student'}: {m['content']}" for m in st.session_state[chat_key]])
                        
                        chat_prompt = f"""
                        You are roleplaying as {target_name}, a {cohort} student. Target Grade: {target_grade}, SEN: {target_sen}.
                        The subject is {subject}. The teacher's name/title is {teacher_name}.
                        
                        Here is the conversation so far:
                        {transcript}
                        
                        CRITICAL RULES:
                        1. Respond to the teacher's last question as {target_name}. Keep it brief. 
                        2. Determine the student's current emotion based on the scenario and teacher's prompt. Pick ONE: [neutral, angry, defensive, sad, bored, hesitant, excited, eager].
                        3. You MUST return your response as a raw JSON object with two keys: "dialogue" and "emotion".
                        
                        Example Format:
                        {{"dialogue": "I think it's 4, {teacher_name}", "emotion": "hesitant"}}
                        """
                        
                        try:
                            model = genai.GenerativeModel('gemini-2.5-pro')
                            response = model.generate_content(chat_prompt, generation_config={"response_mime_type": "application/json"})
                            
                            ai_data = json.loads(response.text)
                            reply_text = ai_data.get("dialogue", "...")
                            current_emotion = ai_data.get("emotion", "neutral")
                            
                            st.session_state[chat_key].append({"role": "student", "content": reply_text})
                            
                            active_pitch, active_rate = calculate_emotion_modifiers(base_pitch, base_rate, current_emotion)
                            st.toast(f"Student Mood: {current_emotion.upper()} 🎭")
                            
                            audio_bytes = get_azure_audio(reply_text, student_voice_name, pitch=active_pitch, rate=active_rate)
                            if audio_bytes is None:
                                st.stop()
                            else:
                                st.session_state["latest_audio"] = audio_bytes
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate response: {e}")
                    
