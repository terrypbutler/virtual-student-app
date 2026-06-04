import streamlit as st
import google.generativeai as genai
import json
import time
from PIL import Image
import PyPDF2
import docx

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

def render_stress_tester(df, cohort, subject="General"):
    st.subheader(f"🌩️ Lesson Plan Stress-Tester: {cohort} {subject}")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API Key missing. Please add it to your secrets.toml file.")
        return
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # --- THE SIDEBAR LEGEND (Framework Clarity) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧬 Simulation Frameworks")
    st.sidebar.caption(
        "This stress-test evaluates your lesson against standard UK ITT Core Content Framework metrics:\n\n"
        "* **Rosenshine's Principles:** Small steps modeling, guided practice, active checks.\n"
        "* **Cognitive Load Theory (Sweller):** Working memory optimization & schema integration.\n"
        "* **Tom Sherrington's 'First Principles':** Explicit teaching mechanics.\n"
        "* **Adaptive Teaching:** Differentiation by scaffolding rather than task-splitting."
    )

    # --- 1. THE INPUT AREA ---
    st.markdown("### 1. Provide the Lesson Plan")
    lesson_text = st.text_area("Paste your lesson plan phases, notes, or learning objectives here (Optional if uploading a file):", height=150)
    uploaded_file = st.file_uploader("Upload your Lesson Plan document (PDF, Word, TXT, or Image):", type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'])
    
    extracted_text = ""
    image_parts = []

    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        
        if file_ext in ["png", "jpg", "jpeg"]:
            st.image(uploaded_file, caption="Lesson Plan Resource Scan", use_container_width=True)
            image_parts.append(Image.open(uploaded_file))
            
        elif file_ext == "pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text() + "\n"
                st.success(f"📄 Extracted data from PDF.")
            except Exception as e:
                st.error(f"Error reading PDF: {e}")
                
        elif file_ext == "docx":
            try:
                doc = docx.Document(uploaded_file)
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
                st.success("📄 Extracted data from Word Document.")
            except Exception as e:
                st.error(f"Error reading Word document: {e}")
                
        elif file_ext == "txt":
            extracted_text = uploaded_file.getvalue().decode("utf-8")
            st.success("📄 Extracted data from text file.")

    st.markdown("---")
    
    if not lesson_text and not uploaded_file:
        st.info("👆 Please upload a plan or type your objective above to begin.")
        return

    final_lesson_content = f"{lesson_text}\n\n{extracted_text}".strip()

    # --- 2. EXECUTE THE STRESS TEST ---
    if st.button("🚀 Stress-Test Lesson", type="primary", use_container_width=True):
        with st.spinner(f"Simulating the lesson against student profiles and passports..."):
            
            # Compile complete student profiles including deep Passport contexts
            age_context = "11 to 12 years old" if cohort == "Year 7" else "14 to 15 years old"
            profiles = []
            for _, row in df.iterrows():
                name = row.get("Full Name", "Unknown")
                grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
                sen = get_flexible_text(row, ["SEN Status", "SEND Status", "SEN Detail"])
                eal = get_flexible_text(row, ["EAL", "EAL Status"])
                math_score = get_flexible_text(row, ["KS2 Maths", "KS2 Math", "SATs Maths"])
                read_score = get_flexible_text(row, ["KS2 Read", "KS2 Reading", "SATs Reading"])
                susp = get_flexible_text(row, ["Suspension days", "Suspensions"])
                
                # GRABBING DEEP PASSPORT DATA:
                home_passport = get_flexible_text(row, ["Home Life & Interests", "Home Life", "Interests"])
                
                profiles.append(
                    f"- {name} | Target Grade: {grade} | KS2 Read Score: {read_score} | KS2 Math Score: {math_score} | "
                    f"SEN Support: {sen} | EAL Status: {eal} | Past Suspensions: {susp} | "
                    f"STUDENT PASSPORT (Home Context & Key Traits): {home_passport}"
                )
            profiles_text = "\n".join(profiles)

            system_prompt = f"""
            You are an elite UK Higher Education Initial Teacher Training (ITT) tutor and curriculum mentor.
            You are conducting a lesson simulation audit for a trainee's lesson plan.
            Subject: {subject}. Cohort: {cohort} (Age range: {age_context}).
            
            You must evaluate this lesson plan against the complete data profiles and Student Passports of these {len(df)} students:
            {profiles_text}
            
            TRAINEE'S LESSON PLAN INPUT:
            {final_lesson_content}
            
            ASSESSMENT MODEL OBJECTIVES:
            1. Rosenshine's Principles of Instruction: Verify if complex tasks are broken down into small, digestible chunks with active modeling.
            2. Cognitive Load Theory (Sweller): Identify hidden memory bottle-necks, lack of procedural automaticity, or layout/presentation overload.
            3. Tom Sherrington's 'First Principles' of Teaching: Audit the transition formatting between instructional teaching, guided practice, and independent application.
            4. Adaptive Teaching & Inclusion: Cross-reference the timeline against Student Passports (SEN/EAL/Disadvantaged). Determine if the lesson scaffolds UP for inclusivity, or falls into the trap of low expectations.

            TECHNICAL COMPLIANCE RULE: You must return ONLY a clean JSON object using this exact structure:
            {{
              "metrics": {{
                "predicted_mastery_count": <int>,
                "high_risk_overload_count": <int>,
                "pacing_warning_label": "<Keep this extremely short: e.g., 'Stable', 'Pacing Risk: Phase 2', 'Early Finishers High'>",
                "pacing_detailed_desc": "<1 sentence detailing the pacing and transition flow behavior>"
              }},
              "critique": {{
                "modeling": "<1-2 sentences critiquing modeling via Rosenshine/Sherrington models>",
                "guided_practice": "<1-2 sentences evaluating the fading of scaffolding>",
                "checking_for_understanding": "<1-2 sentences auditing the AfL tracking mechanisms>"
              }},
              "focus_group": [
                {{
                  "name": "<Exact student name>",
                  "profile_type": "<e.g., SEN Support Passport, High Attainer Passport>",
                  "experience": "<1-2 sentences detailing how their passport needs and prior attainment will manifest in this specific lesson timeline>"
                }}
              ],
              "actionable_tweaks": [
                "<Actionable pedagogical change 1>",
                "<Actionable pedagogical change 2>",
                "<Actionable pedagogical change 3>"
              ]
            }}
            * Ensure the focus_group contains exactly 4 distinct students selected out of the class list.
            """

            model = genai.GenerativeModel('gemini-2.5-pro')
            contents = [system_prompt]
            if image_parts:
                contents.extend(image_parts)

            try:
                response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
                raw_json = response.text.replace("```json", "").replace("```", "").strip()
                result = json.loads(raw_json)
                
                # --- 3. RENDER THE DASHBOARD ---
                st.success("✅ Simulation Matrix Compiled!")
                
                # Zone 1: Metrics (REWORKED TEXT WRAPPING)
                st.markdown("### 📊 Class Survival Metrics")
                metrics = result.get("metrics", {})
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted Mastery", f"{metrics.get('predicted_mastery_count', 0)} / {len(df)}")
                m2.metric("Working Memory Overload", f"{metrics.get('high_risk_overload_count', 0)} Students", delta="Scaffolding Required", delta_color="inverse")
                m3.metric("Pacing Status", metrics.get('pacing_warning_label', 'Review Flow'))
                
                # Safe typography injection for the descriptive text block under the metrics row
                if "pacing_detailed_desc" in metrics:
                    st.markdown(f"⏱️ **Pacing Analysis:** *{metrics.get('pacing_detailed_desc')}*")
                
                st.divider()
                
                # Zone 2: Pedagogy Critique
                st.markdown("### 🧠 'First Principles' Theoretical Critique")
                critique = result.get("critique", {})
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.info(f"**Modeling & Schema (Rosenshine)**\n\n{critique.get('modeling', 'N/A')}")
                with c2:
                    st.warning(f"**Guided Practice Mechanics**\n\n{critique.get('guided_practice', 'N/A')}")
                with c3:
                    st.success(f"**AfL Checkpoints (Sherrington)**\n\n{critique.get('checking_for_understanding', 'N/A')}")
                
                st.divider()
                
                # Zone 3: Focus Group
                st.markdown("### 🔬 Student Passport Focus Group")
                st.caption("How specific student passports cross-referenced with prior attainment interact with your plan:")
                focus_group = result.get("focus_group", [])
                
                cols = st.columns(2)
                for idx, student in enumerate(focus_group[:4]):
                    col = cols[idx % 2]
                    with col:
                        with st.expander(f"👤 {student.get('name', 'Student')} — {student.get('profile_type', 'Passport Profile')}", expanded=True):
                            st.write(student.get("experience", "No data compiled."))
                            
                st.divider()
                
                # Zone 4: Actionable Tweaks
                st.markdown("### 🛠️ The 'S-Plan' Recommended Interventions")
                tweaks = result.get("actionable_tweaks", [])
                for i, tweak in enumerate(tweaks):
                    st.markdown(f"**{i+1}.** {tweak}")

            except Exception as e:
                st.error(f"Failed to compile the dashboard structure. Error: {e}")
