import streamlit as st
import random
from modules.photo_utils import display_student_photo

def get_flexible_text(row, possible_names):
    """Extracts text flexibly handling variations in column names."""
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
    """Helper function to calculate the red/green/blue dots for a given student."""
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

def render_seating_plan(df, cohort):
    st.subheader("⚡ Visual Classroom Planner")
    
    rows, cols = 5, 6
    if 'seats' not in st.session_state: st.session_state.seats = {}
    
    # 1. Determine who is seated and who is unassigned
    all_students = df["Full Name"].tolist()
    assigned_students = [s for s in st.session_state.seats.values() if s != "Empty"]
    unassigned_students = [s for s in all_students if s not in assigned_students]

    # --- TOP CONTROLS & NEXT UP SPOTLIGHT ---
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown("### 👤 Up Next")
        st.markdown("<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 2px solid #3498db;'>", unsafe_allow_html=True)
        if unassigned_students:
            next_student = unassigned_students[0]
            display_student_photo(next_student, cohort)
            
            dots = get_student_dots(next_student, df)
            dot_html = f"<div style='text-align: center; font-size: 16px; margin: 5px 0;'>{dots}</div>" if dots else "<div style='margin: 5px 0;'>&nbsp;</div>"
            
            st.markdown(f"<h4 style='text-align:center; margin-top:0px; font-size: 14px;'>{next_student}</h4>{dot_html}", unsafe_allow_html=True)
            st.caption(f"**{len(unassigned_students)}** left to place.")
        else:
            st.success("✅ All seated!")
            next_student = None
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 🪑 Classroom Grid")
        
        # Auto-Fill & Clear Tools
        tools_c1, tools_c2, tools_c3 = st.columns([1, 1, 2])
        with tools_c1:
            if st.button("🪄 Auto-Fill", use_container_width=True):
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
        
        # --- THE VISUAL GRID ---
        for r in range(rows):
            row_cols = st.columns(cols)
            for c in range(cols):
                seat_key = f"seat_{r}_{c}"
                current_val = st.session_state.seats.get(seat_key, "Empty")
                
                with row_cols[c]:
                    # Create a distinct visual box for every seat
                    st.markdown("<div style='border: 1px solid #ddd; border-radius: 8px; padding: 5px; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: white;'>", unsafe_allow_html=True)
                    
                    if current_val == "Empty":
                        # Render Empty Seat Button
                        st.markdown("<div style='height: 100px; display: flex; align-items: center; justify-content: center; color: #ccc;'><em>Empty Seat</em></div>", unsafe_allow_html=True)
                        if st.button("➕ Place", key=seat_key, use_container_width=True, type="secondary"):
                            if next_student:
                                st.session_state.seats[seat_key] = next_student
                                st.rerun()
                    else:
                        # Render Occupied Seat (Photo + Dots + Name + Remove Button)
                        display_student_photo(current_val, cohort)
                        
                        dots = get_student_dots(current_val, df)
                        if dots:
                            st.markdown(f"<div style='text-align: center; font-size: 12px; margin: 2px 0;'>{dots}</div>", unsafe_allow_html=True)
                        
                        st.markdown(f"<div style='text-align: center; font-size: 11px; font-weight: bold; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin-bottom: 5px;'>{current_val}</div>", unsafe_allow_html=True)
                        
                        if st.button("❌", key=f"remove_{r}_{c}", use_container_width=True):
                            st.session_state.seats[seat_key] = "Empty"
                            st.rerun()
                            
                    st.markdown("</div>", unsafe_allow_html=True)
