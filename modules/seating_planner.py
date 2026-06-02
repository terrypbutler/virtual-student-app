import streamlit as st
import random
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

def render_seating_plan(df, cohort):
    st.subheader("⚡ Fast Classroom Planner")
    
    rows, cols = 5, 6
    if 'seats' not in st.session_state: st.session_state.seats = {}
    
    # 1. Determine who is seated and who is unassigned
    all_students = df["Full Name"].tolist()
    assigned_students = [s for s in st.session_state.seats.values() if s != "Empty"]
    unassigned_students = [s for s in all_students if s not in assigned_students]

    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN", "0", "0.0"]

    # --- TOP CONTROLS & NEXT UP SPOTLIGHT ---
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### 👤 Up Next")
        if unassigned_students:
            next_student = unassigned_students[0]
            student_row = df[df["Full Name"] == next_student].iloc[0]
            
            display_student_photo(next_student, cohort)
            st.markdown(f"<h4 style='text-align:center; margin-top:5px;'>{next_student}</h4>", unsafe_allow_html=True)
            
            # Quick status dots
            sen = get_flexible_text(student_row, ["SEN Status", "SEND Status"]) or ""
            pp = get_flexible_text(student_row, ["Disadvantaged (PP)", "PP"]) or ""
            eal = get_flexible_text(student_row, ["EAL", "EAL Status"]) or ""
            
            dots = []
            if sen.upper() not in ignore_list: dots.append("🔴 SEND")
            if eal.upper() not in ignore_list: dots.append("🟢 EAL")
            if pp.upper() not in ignore_list: dots.append("🔵 PP")
            
            if dots:
                st.markdown(f"<div style='text-align: center; font-size: 12px; font-weight:bold;'>{' | '.join(dots)}</div>", unsafe_allow_html=True)
            
            st.caption(f"{len(unassigned_students)} students remaining.")
        else:
            st.success("✅ All students seated!")
            next_student = None

    with col2:
        st.markdown("### 🪑 Classroom Grid")
        st.caption("Click any empty seat to place the 'Up Next' student. Click an occupied seat to remove them.")
        
        # Auto-Fill Tools
        tools_c1, tools_c2, tools_c3 = st.columns(3)
        with tools_c1:
            if st.button("🪄 Auto-Fill Remaining", use_container_width=True):
                available_seats = [f"seat_{r}_{c}" for r in range(rows) for c in range(cols) if st.session_state.seats.get(f"seat_{r}_{c}", "Empty") == "Empty"]
                random.shuffle(unassigned_students)
                for i, student in enumerate(unassigned_students):
                    if i < len(available_seats):
                        st.session_state.seats[available_seats[i]] = student
                st.rerun()
        with tools_c2:
            if st.button("🗑️ Clear Room", use_container_width=True):
                st.session_state.seats = {}
                st.rerun()

        st.markdown("---")
        
        # The Grid
        for r in range(rows):
            row_cols = st.columns(cols)
            for c in range(cols):
                seat_key = f"seat_{r}_{c}"
                current_val = st.session_state.seats.get(seat_key, "Empty")
                
                btn_type = "primary" if current_val != "Empty" else "secondary"
                
                with row_cols[c]:
                    if st.button(current_val if current_val != "Empty" else "+", key=seat_key, use_container_width=True, type=btn_type):
                        if current_val != "Empty": 
                            # Remove student from seat
                            st.session_state.seats[seat_key] = "Empty"
                            st.rerun()
                        elif next_student:
                            # Assign the 'Up Next' student to this empty seat
                            st.session_state.seats[seat_key] = next_student
                            st.rerun()
