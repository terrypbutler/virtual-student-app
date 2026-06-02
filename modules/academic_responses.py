import streamlit as st
import google.generativeai as genai
import json
import random
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

def fetch_ai_answers(question, student_subset, instructions, uploaded_file):
    """Centralized function to call Gemini and return a dictionary of answers."""
    # Build the profile list
    profiles = []
    for _, row in student_subset.iterrows():
        name = row.get("Full Name")
        grade = get_flexible_text(row, ["Projected Grade", "Predicted Grade"])
        sen = get_flexible_text(row, ["SEN Status", "SEND Status"])
        eal = get_flexible_text(row, ["EAL", "EAL Status"])
        profiles.append(f"- {name} (Target: {grade}, SEN: {sen}, EAL: {eal})")
        
    profiles_text = "\n".join(profiles)
    
    prompt = f"""
    The teacher has asked the class: "{question}"
    
    Here is the list of specific students answering:
    {profiles_text}
    
    {instructions}
    
    CRITICAL: If the answer requires mathematics, format it simply using standard keyboard symbols (like x^2) or Unicode (like x²). Do not use complex LaTeX.
    CRITICAL: Return ONLY a valid JSON dictionary where the keys are the exact student names and the values are their answers. Do not include any other text.
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    contents = [prompt]
    if uploaded_file is not None:
        contents.append(Image.open(uploaded_file))
        
    response = model.generate_content(
        contents, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Clean and parse the JSON safely
    try:
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        st.error("Failed to parse AI response. Please try asking again.")
        return {}

def render_academic_responses(df, cohort):
    st.subheader("🎓 AfL Simulator: Academic Questioning")
    
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
    
    # Check if a question is asked before running any mode
    if not teacher_question:
        st.info("👆 Please type a question above to begin.")
        return

    # --- MODE: MINI-WHITEBOARDS ---
    if mode == "📝 Mini-Whiteboards (Whole Class)":
        st.caption("Scans the whole room for quick, short-form answers.")
        if st.button("Show All Mini-Whiteboards", type="primary"):
            with st.spinner("Students are writing..."):
                instructions = "Generate a realistic, short answer (maximum 6 words) for EACH student based on their profile. Include common misconceptions for lower grades."
                answers = fetch_ai_answers(teacher_question, df, instructions, uploaded_file)
                
                # Render Grid
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
        st.caption("Collects a full, detailed paragraph from every student to check deep understanding.")
        if st.button("Collect Exit Tickets", type="primary"):
            with st.spinner("Students are writing their paragraphs..."):
                instructions = "Generate a detailed, full-sentence explanation (2 to 3 sentences) for EACH student. Reflect their predicted grade in the depth and accuracy of their writing."
                answers = fetch_ai_answers(teacher_question, df, instructions, uploaded_file)
                
                st.markdown("### Collected Tickets")
                for _, row in df.iterrows():
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
                # Pick 5 random students
                volunteers_df = df.sample(n=min(5, len(df)))
                instructions = "Generate a spoken, conversational answer for EACH of these volunteering students. They are volunteering, so they generally feel confident, though they might still be slightly wrong."
                answers = fetch_ai_answers(teacher_question, volunteers_df, instructions, uploaded_file)
                
                st.markdown("### 🖐️ Volunteers")
                for _, row in volunteers_df.iterrows():
                    name = row.get("Full Name")
                    ans = answers.get(name, "...")
                    
                    st.markdown(f"""
                        <div style='background-color: #f8f9fa; border-left: 5px solid #f1c40f; padding: 15px; margin-bottom: 10px; border-radius: 4px;'>
                            <strong>{name} raises their hand:</strong> "{ans}"
                        </div>
                    """, unsafe_allow_html=True)

    # --- MODE: COLD CALL ---
    elif mode == "🎯 Cold Call (Targeted)":
        st.caption("Select a specific student and put them on the spot.")
        target_name = st.selectbox("Select student to Cold Call:", df["Full Name"].tolist())
        
        if st.button(f"Ask {target_name}", type="primary"):
            with st.spinner(f"Waiting for {target_name} to answer..."):
                target_df = df[df["Full Name"] == target_name]
                instructions = "Generate a spoken, conversational answer for this specific student. Because they were cold-called, they might hesitate or use filler words ('Umm', 'I think...') depending on their confidence and grade."
                answers = fetch_ai_answers(teacher_question, target_df, instructions, uploaded_file)
                
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
