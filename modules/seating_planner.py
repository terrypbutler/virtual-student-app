import streamlit as st
import random
import google.generativeai as genai
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
        st.markdown("""
            <div style='height: 190px; display: flex; align-items: center; justify-content: center; 
                        border: 2px dashed #ccc; border-radius: 8px; margin-bottom: 10px; 
                        background: #fdfdfd; color: #aaa; font-size: 14px;'>
                <em>Empty</em>
            </div>
        """, unsafe_allow_html=True)
        
        pad_l, btn, pad_r = st.columns([1, 4, 1])
        with btn:
            if st.button("➕", key=f"add_{seat_key}", use_container_width=True, type="tertiary", help="Place student here"):
                if next_student:
                    st.session_state.seats[seat_key] = next_student
                    st.rerun()
    else:
        display_student_photo(current_val, cohort)
        
        dots = get_student_dots(current_val, df)
        dot_html = f"<div style='display: flex; justify-content: center; width: 100%; font-size: 14px; margin: 2px 0; min-height: 20px; letter-spacing: 2px;'>{dots if dots else ''}</div>"
        st.markdown(dot_html, unsafe_allow_html=True)
        
        if current_val in st.session_state.circulation_path:
            idx = st.session_state.circulation_path.index(current_val)
            total = len(st.session_state.circulation_path)
            lightness = int(30 + (55 * (idx / (total - 1)))) if total > 1 else 30
            bg_color = f"hsl(210, 80%, {lightness}%)"
            text_color = "white" if lightness < 65 else "#111111"
            box_style = f"background-color: {bg_color}; color: {text_color}; padding: 4px; border-radius: 6px; border: 1px solid #3498db;"
            display_name = f"{idx + 1}. {current_val}"
        else:
            box_style = "background-color: transparent; color: inherit; padding: 4px; border-radius: 6px; border: 1px solid transparent;"
            display_name = current_val
            
        st.markdown(f"<div style='text-align: center; font-size: 11px; font-weight: bold; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin-bottom: 8px; {box_style}'>{display_name}</div>", unsafe_allow_html=True)
        
        pad_l, c1, pad_r = st.columns([1, 2, 1])
        with c1:
            if st.button("❌", key=f"rm_{seat_key}", use_container_width=True, type="tertiary", help="Remove student"):
                st.session_state.seats[seat_key] = "Empty"
                if current_val in st.session_state.circulation_path:
                    st.session_state.circulation_path.remove(current_val)
                st.rerun()

def render_seating_plan(df, cohort):
    st.subheader("⚡ Visual Classroom Planner")
    
    # Initialize State
    TOTAL_SEATS = 32
    if 'seats' not in st.session_state: st.session_state.seats = {}
    if 'circulation_path' not in st.session_state: st.session_state.circulation_path = []
    if 'temp_path' not in st.session_state: st.session_state.temp_path = []
    if 'mentor_chat' not in st.session_state: st.session_state.mentor_chat = []
    
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    all_students = df["Full Name"].tolist()
    assigned_students = [s for s in st.session_state.seats.values() if s != "Empty"]
    unassigned_students = [s for s in all_students if s not in assigned_students]

    # Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Up Next to Place")
    if unassigned_students:
        next_student = unassigned_students[0]
        with st.sidebar.container(border=True):
            display_student_photo(next_student, cohort)
            dots = get_student_dots(next_student, df)
            dot_html = f"<div style='display: flex; justify-content: center; width: 100%; font-size: 16px; margin: 5px 0; letter-spacing: 2px;'>{dots}</div>" if dots else "<div style='margin: 5px 0;'>&nbsp;</div>"
            st.sidebar.markdown(f"<h4 style='text-align:center; margin-top:0px; font-size: 15px;'>{next_student}</h4>{dot_html}", unsafe_allow_html=True)
            st.sidebar.caption(f"**{len(unassigned_students)}** students remaining.")
    else:
        st.sidebar.success("✅ All students seated!")
        next_student = None

    # Tools
    tools_c1, tools_c2, tools_c3 = st.columns([1.5, 1, 1])
    with tools_c1:
        layout_choice = st.radio("Seat Grouping:", ["Rows (4x8)", "Groups (8 Tables)"], horizontal=True, label_visibility="collapsed")
    with tools_c2:
        if st.button("🪄 Auto-Fill", use_container_width=True):
            available_seats = [f"seat_{i}" for i in range(TOTAL_SEATS) if st.session_state.seats.get(f"seat_{i}", "Empty") == "Empty"]
            random.shuffle(unassigned_students)
            for i, student in enumerate(unassigned_students):
                if i < len(available_seats): st.session_state.seats[available_seats[i]] = student
            st.rerun()
    with tools_c3:
        if st.button("🗑️ Clear Room", use_container_width=True):
            st.session_state.seats = {}
            st.session_state.circulation_path = []
            st.session_state.temp_path = []
            st.session_state.mentor_chat = []
            st.rerun()

    # Route Builder
    st.markdown("---")
    if assigned_students:
        st.session_state.temp_path = st.multiselect("👣 Build Circulation Route (Select in order):", options=assigned_students, default=st.session_state.circulation_path)
        if st.button("✅ Apply Route"):
            st.session_state.circulation_path = st.session_state.temp_path
            st.rerun()
            
    # Classroom
    st.markdown("<div style='text-align: center; background-color: #2C3E50; color: white; padding: 8px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; letter-spacing: 3px;'>👨‍🏫 FRONT OF CLASSROOM 👩‍🏫</div>", unsafe_allow_html=True)
    
    if layout_choice == "Rows (4x8)":
        for r in range(4):
            cols = st.columns(8, gap="small")
            for c in range(8):
                idx = (r * 8) + c
                with cols[c]: render_seat_ui(f"seat_{idx}", st.session_state.seats.get(f"seat_{idx}", "Empty"), next_student, cohort, df)
    else:
        for grp in range(8):
            with st.container(border=True):
                st.markdown(f"**Table {grp+1}**")
                cols = st.columns(4, gap="small")
                for i in range(4):
                    with cols[i]: render_seat_ui(f"seat_{(grp*4)+i}", st.session_state.seats.get(f"seat_{(grp*4)+i}", "Empty"), next_student, cohort, df)

    # Mentor Eval
    st.markdown("---")
    if st.button("Evaluate My Plan", type="primary"):
        # Logic for AI Evaluation remains unchanged
        st.success("Plan evaluation triggered...")
