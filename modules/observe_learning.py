import streamlit as st
import google.generativeai as genai
import json
import random
import re
from modules.photo_utils import display_student_photo

try:
    from modules.academic_responses import get_elevenlabs_audio
except ImportError:
    st.error("⚠️ Could not find get_elevenlabs_audio.")

def get_flexible_text(row, possible_names):
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                if val.endswith(".0"): val = val[:-2]
                return val
    return "None recorded"

def render_observation_room(df, cohort):
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("👁️ Circulate the Room: Full Class Observation")
    with col_header2:
        enable_voice = st.toggle("🔊 Voice Audio", value=True, key="obs_voice_toggle")

    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing.")
        return
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # --- 1. INITIALIZE THE STATE MACHINE ---
    if "obs_task" not in st.session_state: st.session_state.obs_task = ""
    if "live_observations" not in st.session_state: st.session_state.live_observations = {}
    if "obs_intervene_target" not in st.session_state: st.session_state.obs_intervene_target = None
    if "obs_active_students" not in st.session_state: st.session_state.obs_active_students = []
    
    if "student_states" not in st.session_state: st.session_state.student_states = {}

    # --- 2. THE INTERVENTION VIEW ---
    if st.session_state.obs_intervene_target:
        target_name = st.session_state.obs_intervene_target
        observation = st.session_state.live_observations.get(target_name, "")
        current_mot = st.session_state.student_states[target_name]["motivation"]
        
        st.markdown(f"### 🛑 Intervening with {target_name}")
        st.info(f"**Current Task:** {st.session_state.obs_task}\n\n**You observed:** {observation}")
        
        chat_key = f"obs_chat_{target_name}"
        if chat_key not in st.session_state: st.session_state[chat_key] = []

        col_a, col_b = st.columns([1, 3])
        with col_a:
            display_student_photo(target_name, cohort)
            st.metric("Current Motivation", f"{current_mot}%")
            if st.button("🔙 Step Away (Back to Room)", use_container_width=True):
                st.session_state.obs_intervene_target = None
                st.rerun()

        with col_b:
            if "latest_audio_obs" in st.session_state:
                st.audio(st.session_state["latest_audio_obs"], format="audio/mp3", autoplay=True)
                del st.session_state["latest_audio_obs"]

            for msg in st.session_state[chat_key]:
                with st.chat_message(msg["role"]): st.write(msg["content"])

            teacher_input = st.chat_input(f"Approach {target_name} and say...")

            if teacher_input:
                st.session_state[chat_key].append({"role": "user", "content": teacher_input})
                with st.chat_message("user"): st.write(teacher_input)

                target_row = df[df["Full Name"] == target_name].iloc[0]
                age = "11" if cohort == "Year 7" else "15"
                sen = get_flexible_text(target_row, ["SEN Status", "SEND Status", "SEN Detail"])
                eal = get_flexible_text(target_row, ["EAL", "EAL Status"])
                grade = get_flexible_text(target_row, ["Projected Grade", "Predicted Grade"])
                susp = get_flexible_text(target_row, ["Suspension days", "Suspensions"])
                
                transcript = "\n".join([f"{'Teacher' if m['role']=='user' else target_name}: {m['content']}" for m in st.session_state[chat_key]])

                system_prompt = (
                    f"You are roleplaying as a {age}-year-old UK student named {target_name}.\n"
                    f"Data: SEN: {sen} | EAL: {eal} | Grade: {grade} | Suspensions: {susp}\n"
                    f"Task: '{st.session_state.obs_task}'\n"
                    f"Your current internal motivation level is {current_mot}/100.\n\n"
                    f"Transcript:\n{transcript}\n\n"
                    "CRITICAL RULES:\n"
                    "1. Evaluate the teacher's last statement. Is it specific praise, helpful scaffolding, dismissive, or overly harsh?\n"
                    "2. Based on their pedagogy, determine how this affects your motivation. Create a 'motivation_delta' integer between -25 (terrible) and +35 (great).\n"
                    f"3. Respond verbally as {target_name}. Include non-verbal actions in asterisks (e.g., *smiles*, *looks away*).\n"
                    "4. Pick ONE emotion: [neutral, defensive, embarrassed, frustrated, bored, proud, eager].\n"
                    "5. Return ONLY a raw JSON object with keys: \"dialogue\", \"emotion\", and \"motivation_delta\".\n\n"
                    "Example:\n"
                    "{\"dialogue\": \"*sits up straighter* Thanks sir, I'll try that.\", \"emotion\": \"eager\", \"motivation_delta\": 20}"
                )

                with st.spinner(f"{target_name} is reacting..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(system_prompt, generation_config={"response_mime_type": "application/json"})
                        
                        raw_text = response.text.replace("```json", "").replace("```", "")
                        ai_data = json.loads(raw_text.strip())

                        display_text = ai_data.get("dialogue", "...")
                        current_emotion = ai_data.get("emotion", "neutral")
                        delta = int(ai_data.get("motivation_delta", 0))
                        
                        new_mot = min(100, max(0, current_mot + delta))
                        st.session_state.student_states[target_name]["motivation"] = new_mot
                        
                        if delta > 0:
                            st.success(f"📈 Great pedagogy! Motivation increased by {delta}% (Now {new_mot}%)")
                        elif delta < 0:
                            st.error(f"📉 That missed the mark. Motivation dropped by {abs(delta)}% (Now {new_mot}%)")
                        else:
                            st.info(f"➖ Neutral interaction. Motivation unchanged.")
                        
                    except Exception as e:
                        st.error(f"Gemini Error: {e}")
                        st.stop()

                st.session_state[chat_key].append({"role": "assistant", "content": display_text})
                with st.chat_message("assistant"): st.write(display_text)

                audio_text = re.sub(r'[*\[(].*?[*\])]', '', display_text).strip()

                if enable_voice and audio_text:
                    student_voice_id = target_row.get("Voice_Name", "JBFqnCBsd6RMkjVDRZzb")
                    audio_bytes = get_elevenlabs_audio(audio_text, student_voice_id)
                    if audio_bytes:
                        st.session_state["latest_audio_obs"] = audio_bytes
                        
                st.rerun()

    # --- 3. THE ROOM VIEW ---
    else:
        st.markdown("### 1. Set the Independent Task")
        current_task = st.text_area("Describe the task:", placeholder="e.g., 'Draft a 10-line poem.'", value=st.session_state.obs_task)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Initialize Full Class", type="primary", use_container_width=True):
                if not current_task:
                    st.warning("Please set a task first.")
                    st.stop()
                    
                st.session_state.obs_task = current_task
                # NO MORE SAMPLING: Use the entire dataframe!
                st.session_state.obs_active_students = df["Full Name"].tolist()
                
                for _, row in df.iterrows():
                    name = row["Full Name"]
                    grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
                    sen = get_flexible_text(row, ["SEN Status", "SEND Status"])
                    
                    st.session_state.student_states[name] = {
                        "motivation": random.randint(60, 90) if "7" in grade or "8" in grade or "9" in grade else random.randint(30, 60),
                        "progress": 0,
                        "decay_rate": random.randint(10, 20) if sen and sen.upper() != "NONE" else random.randint(5, 12)
                    }
                
                st.session_state.live_observations = {name: "Starting the task." for name in st.session_state.obs_active_students}
                st.rerun()

        with col2:
            if st.session_state.obs_active_students:
                if st.button("⏱️ Advance Time (5 Mins) & Scan Full Room", use_container_width=True):
                    for name in st.session_state.obs_active_students:
                        stats = st.session_state.student_states[name]
                        stats["motivation"] = max(0, stats["motivation"] - stats["decay_rate"])
                        if stats["motivation"] > 40:
                            stats["progress"] = min(100, stats["progress"] + random.randint(10, 25))

                    profiles = []
                    for name in st.session_state.obs_active_students:
                        mot = st.session_state.student_states[name]["motivation"]
                        prog = st.session_state.student_states[name]["progress"]
                        profiles.append(f"- {name} | Motivation: {mot}% | Progress: {prog}%")
                    
                    obs_prompt = (
                        f"Task: '{current_task}'\n"
                        f"Generate a 1-sentence physical observation of each student based on their numbers.\n"
                        f"{chr(10).join(profiles)}\n\n"
                        "RULES: If motivation > 70%, they are focused. If 40-70%, they are slowing down/distracted. If <40%, they are completely off-task or acting out. If progress is 100%, they are finished.\n"
                        "Return a ONLY a raw JSON dict with names as keys and observations as values."
                    )
                    
                    # Warn the user that a full class takes a few extra seconds
                    with st.spinner(f"Scanning {len(st.session_state.obs_active_students)} students... (this may take up to 10 seconds)"):
                        try:
                            model = genai.GenerativeModel('gemini-2.5-flash')
                            response = model.generate_content(obs_prompt, generation_config={"response_mime_type": "application/json"})
                            raw_text = response.text.replace("```json", "").replace("```", "")
                            st.session_state.live_observations = json.loads(raw_text.strip())
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed scan: {e}")

        st.markdown("---")

        if st.session_state.obs_active_students:
            st.markdown("### 2. Live Room Status")
            
            # --- CLASS AVERAGES DASHBOARD ---
            total_mot = sum(st.session_state.student_states[name]["motivation"] for name in st.session_state.obs_active_students)
            total_prog = sum(st.session_state.student_states[name]["progress"] for name in st.session_state.obs_active_students)
            avg_mot = int(total_mot / len(st.session_state.obs_active_students))
            avg_prog = int(total_prog / len(st.session_state.obs_active_students))
            
            dash_col1, dash_col2, dash_col3 = st.columns(3)
            with dash_col1:
                st.metric("Class Average Motivation", f"{avg_mot}%")
            with dash_col2:
                st.metric("Class Average Progress", f"{avg_prog}%")
            with dash_col3:
                st.metric("Students Monitored", len(st.session_state.obs_active_students))
                
            st.markdown("---")
            
            # Grid tightened to 4 columns to fit more students on screen
            num_cols = 4
            for i in range(0, len(st.session_state.obs_active_students), num_cols):
                cols = st.columns(num_cols)
                for idx, student_name in enumerate(st.session_state.obs_active_students[i : i + num_cols]):
                    with cols[idx]:
                        with st.container(border=True):
                            display_student_photo(student_name, cohort)
                            st.markdown(f"**{student_name}**")
                            
                            stats = st.session_state.student_states[student_name]
                            
                            mot_color = "🟢" if stats["motivation"] > 65 else "🟡" if stats["motivation"] > 35 else "🔴"
                            st.caption(f"{mot_color} **Drive:** {stats['motivation']}% | 📋 **Done:** {stats['progress']}%")
                            
                            obs_text = st.session_state.live_observations.get(student_name, "Waiting for scan...")
                            st.info(f"*{obs_text}*")
                            
                            if st.button("🗣️ Intervene", key=f"int_{student_name}", use_container_width=True):
                                st.session_state.obs_intervene_target = student_name
                                st.rerun()
