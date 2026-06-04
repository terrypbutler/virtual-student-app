import streamlit as st
import google.generativeai as genai
import json
import time
from PIL import Image

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

def render_stress_tester(df, cohort, subject="General"):
    st.subheader(f"🌩️ Lesson Plan Stress-Tester: {cohort} {subject}")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing. Please add it to your secrets.toml file.")
        return
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # --- 1. THE INPUT AREA ---
    st.markdown("### 1. Provide the Lesson Plan")
    lesson_text = st.text_area("Paste the lesson plan, activities, or learning objectives here:", height=150)
    uploaded_file = st.file_uploader("Or upload a photo/screenshot of the plan:", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Lesson Plan Resource", use_container_width=True)

    st.markdown("---")
    
    if not lesson_text and not uploaded_file:
        st.info("👆 Please provide lesson plan text or upload an image to begin.")
        return

    # --- 2. EXECUTE THE STRESS TEST ---
    if st.button("🚀 Stress-Test Lesson", type="primary", use_container_width=True):
        with st.spinner(f"Simulating the lesson with all {len(df)} students..."):
            
            # Extract class data
            age_context = "11 to 12 years old" if cohort == "Year 7" else "14 to 15 years old"
            profiles = []
            for _, row in df.iterrows():
                name = row.get("Full Name", "Unknown")
                grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
                sen = get_flexible_text(row, ["SEN Status", "SEND Status", "SEN Detail"])
                eal = get_flexible_text(row, ["EAL", "EAL Status"])
                read_score = get_flexible_text(row, ["KS2 Read", "KS2 Reading", "SATs Reading"])
                susp = get_flexible_text(row, ["Suspension days", "Suspensions"])
                profiles.append(f"- {name} | Target: {grade} | SEN: {sen} | EAL: {eal} | KS2 Read: {read_score} | Susp: {susp}")
            profiles_text = "\n".join(profiles)

            # Build the System Prompt
            system_prompt = f"""
            You are an expert teacher trainer evaluating a trainee teacher's lesson plan. 
            Subject: {subject}. Cohort: {cohort} (Age {age_context}).
            
            Here is the detailed profile of the {len(df)} students in the class:
            {profiles_text}
            
            LESSON PLAN INFO:
            {lesson_text}
            
            Your job is to stress-test this lesson plan by predicting how this specific cohort will experience it, grounding your evaluation in Rosenshine's Principles of Instruction and Cognitive Load Theory.
            
            CRITICAL LENS:
            - Modeling: Does the plan break concepts down enough for the lowest prior-attainers?
            - Guided Practice: Is there sufficient scaffolding? Will fading be too abrupt for SEN students?
            - Checking for Understanding: Are there explicit checkpoints to verify learning?
            
            CRITICAL TECHNICAL RULE: Return ONLY a valid JSON object matching this exact schema:
            {{
              "metrics": {{
                "predicted_mastery_count": <int>,
                "high_risk_overload_count": <int>,
                "pacing_warning": "<Short string summarizing pacing risk>"
              }},
              "critique": {{
                "modeling": "<1-2 sentences critiquing modeling>",
                "guided_practice": "<1-2 sentences critiquing guided practice>",
                "checking_for_understanding": "<1-2 sentences evaluating AfL>"
              }},
              "focus_group": [
                {{
                  "name": "<Exact student name from data>",
                  "profile_type": "<e.g., SEN Support, High-Attainer>",
                  "experience": "<1-2 sentences describing how they will struggle or succeed>"
                }}
              ],
              "actionable_tweaks": [
                "<Concrete tweak 1>",
                "<Concrete tweak 2>",
                "<Concrete tweak 3>"
              ]
            }}
            * Ensure the focus_group contains exactly 4 distinct students from the provided list.
            """

            # Call Gemini Pro
            model = genai.GenerativeModel('gemini-2.5-pro')
            contents = [system_prompt]
            if uploaded_file is not None:
                contents.append(Image.open(uploaded_file))

            try:
                response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
                raw_json = response.text.replace("```json", "").replace("
```", "").strip()
                result = json.loads(raw_json)
                
                # --- 3. RENDER THE DASHBOARD ---
                st.success("✅ Simulation Complete!")
                
                # Zone 1: Metrics
                st.markdown("### 📊 Class Survival Metrics")
                metrics = result.get("metrics", {})
                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted to Master Task", f"{metrics.get('predicted_mastery_count', 0)} / {len(df)}")
                m2.metric("High Risk of Overload", f"{metrics.get('high_risk_overload_count', 0)} Students", delta="Review Scaffolding", delta_color="inverse")
                m3.metric("Pacing & Flow", metrics.get('pacing_warning', 'Unknown'))
                
                st.divider()
                
                # Zone 2: Pedagogy Critique
                st.markdown("### 🧠 'First Principles' Critique")
                critique = result.get("critique", {})
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.info(f"**Modeling & Explanations**\n\n{critique.get('modeling', 'N/A')}")
                with c2:
                    st.warning(f"**Guided Practice**\n\n{critique.get('guided_practice', 'N/A')}")
                with c3:
                    st.success(f"**Checking for Understanding**\n\n{critique.get('checking_for_understanding', 'N/A')}")
                
                st.divider()
                
                # Zone 3: Focus Group
                st.markdown("### 🔬 Focus Group Feedback")
                st.caption("How 4 specific students will likely experience this lesson:")
                focus_group = result.get("focus_group", [])
                
                cols = st.columns(2)
                for idx, student in enumerate(focus_group[:4]):
                    col = cols[idx % 2]
                    with col:
                        with st.expander(f"👤 {student.get('name', 'Student')} ({student.get('profile_type', 'Profile')})", expanded=True):
                            st.write(student.get("experience", "No data."))
                            
                st.divider()
                
                # Zone 4: Actionable Tweaks
                st.markdown("### 🛠️ The 'S-Plan' Interventions")
                tweaks = result.get("actionable_tweaks", [])
                for i, tweak in enumerate(tweaks):
                    st.markdown(f"**{i+1}.** {tweak}")

            except Exception as e:
                st.error(f"Failed to generate analysis. Error: {e}")
