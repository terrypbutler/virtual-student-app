import streamlit as st
import random
import google.generativeai as genai
from modules.photo_utils import display_student_photo

# (Keep get_flexible_text, get_student_dots, and render_seat_ui EXACTLY as they were in the previous block)
def get_flexible_text(row, possible_names):
    row_keys = {str(k).strip().lower(): k for k in row.keys()}
    for name in possible_names:
        clean_name = name.lower().strip()
        if clean_name in row_keys:
            val = str(row[row_keys[clean_name]]).strip()
            if val and val.upper() not in ["NAN", "N/A", "NONE", "NULL", ""]:
                if val.endswith(".0"): val = val[:-2]
                return val
    return None

def get_student_dots(student_name, df):
    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN", "0", "0.0"]
    try:
        student_row = df[df["Full Name"] == student_name].iloc[0]
        sen = get_flexible_text(student_row, ["SEN Status", "SEND Status"]) or ""
        pp = get_flexible_text(student_row, ["Disadvantaged (PP)", "PP"]) or ""
        eal = get_flexible_text(student_row, ["EAL", "EAL Status"]) or ""
        
        dots = []
        if sen.upper() not in ignore_list: dots.append("🔴")
        if eal.upper() not in ignore_list: dots.append("🟢")
        if pp.upper() not in ignore_list: dots.append("🔵")
        return " ".join(dots)
    except:
        return ""

def render_seat_ui(seat_key, current_val, next_student, cohort, df):
    if current_val == "Empty":
        st.markdown("<div style='height: 190px; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc; border-radius: 8px; margin-bottom: 10px; background: #fdfdfd; color: #aaa; font-size: 14px;'><em>Empty</em></div>", unsafe_allow_html=True)
        pad_l, btn, pad_r = st.columns([1, 4, 1])
        with btn:
            if st.button("➕", key=f"add_{seat_key}", use_container_width=True, type="tertiary"):
                if next_student:
                    st.session_state.seats[seat_key] = next_student
                    st.rerun()
    else:
        display_student_photo(current_val, cohort)
        dots = get_student_dots(current_val, df)
        st.markdown(f"<div style='display: flex; justify-content: center; width: 100%; font-size: 14px; margin: 2px 0; min-height: 20px; letter-spacing: 2px;'>{dots}</div>", unsafe_allow_html=True)
        
        # Heatmap styling
        box_style = "background-color: transparent; color: inherit; padding: 4px; border-radius: 6px; border: 1px solid transparent;"
        display_name = current_val
        if current_val in st.session_state.circulation_path:
            idx = st.session_state.circulation_path.index(current_val)
            lightness = int(30 + (55 * (idx / (len(st.session_state.circulation_path) - 1)))) if len(st.session_state.circulation_path) > 1 else 30
            box_style = f"background-color: hsl(210, 80%, {lightness}%); color: {'white' if lightness < 65 else '#111'}; padding: 4px; border-radius: 6px;"
            display_name = f"{idx + 1}. {current_val}"
            
        st.markdown(f"<div style='text-align: center; font-size: 11px; font-weight: bold; margin-bottom: 8px; {box_style}'>{display_name}</div>", unsafe_allow_html=True)
        
        pad_l, c1, pad_r = st.columns([1, 2, 1])
        with c1:
            if st.button("❌", key=f"rm_{seat_key}", use_container_width=True, type="tertiary"):
                st.session_state.seats[seat_key] = "Empty"
                if current_val in st.session_state.circulation_path: st.session_state.circulation_path.remove(current_val)
                st.rerun()

def render_seating_plan(df, cohort):
    st.subheader("⚡ Visual Classroom Planner")
    
    # State Init
    if 'seats' not in st.session_state: st.session_state.seats = {}
    if 'circulation_path' not in st.session_state: st.session_state.circulation_path = []
    if 'mentor_chat' not in st.session_state: st.session_state.mentor_chat = []
    
    all_students = df["Full Name"].tolist()
    unassigned = [s for s in all_students if s not in st.session_state.seats.values()]
    next_student = unassigned[0] if unassigned else None

    # [Rest of your UI and Layout code here...]
    # ... (Keep everything from the Tools, Route Builder, and Classroom grid) ...

    # --- AI MENTOR EVALUATION SECTION (FIXED) ---
    st.markdown("---")
    st.subheader("🤖 ITT Mentor: Plan Evaluation")
    
    if st.button("Evaluate My Plan", type="primary"):
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("API Key missing.")
            return

        # Explicitly build the layout map
        layout_text = "Current Classroom Layout:\n"
        for seat, name in st.session_state.seats.items():
            if name != "Empty":
                dots = get_student_dots(name, df)
                layout_text += f"- {name} at {seat} [{dots}]\n"
        
        path_text = " -> ".join(st.session_state.circulation_path) if st.session_state.circulation_path else "No path set."

        with st.spinner("Your mentor is reviewing..."):
            prompt = (
                "**[FICTIONAL SCENARIO - ITT MENTOR]**\n"
                f"{layout_text}\n"
                f"**Route:** {path_text}\n\n"
                "Review the layout and route. 🔴=SEN, 🟢=EAL, 🔵=PP.\n"
                "1. Highlight one strength.\n"
                "2. Ask 1-2 probing questions about student placement or circulation. Keep it brief."
            )
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                if response.text:
                    st.session_state.mentor_chat = [{"role": "assistant", "content": response.text}]
                    st.rerun()
                else:
                    st.error("Mentor didn't reply (Empty response).")
            except Exception as e:
                st.error(f"Mentor AI failed: {e}")
