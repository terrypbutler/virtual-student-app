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

def render_seat_ui(seat_key, current_val, next_student, cohort, df):
    """Helper to consistently render the visual seat box without row jumping."""
    if current_val == "Empty":
        # FIXED HEIGHT PLACEHOLDER: Prevents the rows from collapsing
        st.markdown("""
            <div style='height: 190px; display: flex; align-items: center; justify-content: center; 
                        border: 2px dashed #ccc; border-radius: 8px; margin-bottom: 10px; 
                        background: #fdfdfd; color: #aaa; font-size: 14px;'>
                <em>Empty</em>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Place", key=f"add_{seat_key}", use_container_width=True, type="secondary"):
            if next_student:
                st.session_state.seats[seat_key] = next_student
                st.rerun()
    else:
        # NATIVE STREAMLIT RENDERING: Ensures the images scale safely
        display_student_photo(current_val, cohort)
        
        dots = get_student_dots(current_val, df)
        # min-height ensures that even if a student has NO dots, the name text doesn't jump up
        st.markdown(f"<div style='text-align: center; font-size: 12px; margin: 2px 0; min-height: 18px;'>{dots if dots else ''}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='text-align: center; font-size: 11px; font-weight: bold; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin-bottom: 8px;'>{current_val}</div>", unsafe_allow_html=True)
        
        if st.button("❌ Remove", key=f"rm_{seat_key}", use_container_width=True):
            st.session_state.seats[seat_key] = "Empty"
            st.rerun()


def render_seating_plan(df, cohort):
    st.subheader("⚡ Visual Classroom Planner")
    
    # We standardize on 32 total seats (4x8 rows OR 8 tables of 4)
    TOTAL_SEATS = 32
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
        st.markdown("### 🪑 Classroom Layout")
        
        # Tools & Layout Selector
        tools_c1, tools_c2, tools_c3 = st.columns([1.5, 1, 1])
        with tools_c1:
            layout_choice = st.radio("Seat Grouping:", ["Rows (4x8)", "Groups (8 Tables)"], horizontal=True, label_visibility="collapsed")
        with tools_c2:
            if st.button("🪄 Auto-Fill Room", use_container_width=True):
                available_seats = [f"seat_{i}" for i in range(TOTAL_SEATS) if st.session_state.seats.get(f"seat_{i}", "Empty") == "Empty"]
                random.shuffle(unassigned_students)
                for i, student in enumerate(unassigned_students):
                    if i < len(available_seats):
                        st.session_state.seats[available_seats[i]] = student
                st.rerun()
        with tools_c3:
            if st.button("🗑️ Clear Room", use_container_width=True):
                st.session_state.seats = {}
                st.rerun()

        st.markdown("---")
        
        # --- FRONT OF CLASS BANNER ---
        st.markdown("""
        <div style='text-align: center; background-color: #2C3E50; color: white; padding: 8px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; letter-spacing: 3px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);'>
            👨‍🏫 FRONT OF CLASSROOM (WHITEBOARD) 👩‍🏫
        </div>
        """, unsafe_allow_html=True)
        
        # --- THE VISUAL GRID ---
        if layout_choice == "Rows (4x8)":
            for r in range(4):
                row_cols = st.columns(8, gap="small")
                for c in range(8):
                    seat_idx = (r * 8) + c
                    seat_key = f"seat_{seat_idx}"
                    current_val = st.session_state.seats.get(seat_key, "Empty")
                    
                    with row_cols[c]:
                        render_seat_ui(seat_key, current_val, next_student, cohort, df)
                        
        else:
            # Groups (8 Tables of 4)
            for grp_row in range(2):
                # Apply a medium gap between the large table blocks
                table_cols = st.columns(4, gap="medium")
                for grp_col in range(4):
                    table_idx = (grp_row * 4) + grp_col
                    with table_cols[grp_col]:
                        
                        # Native Streamlit border container to strictly group the 4 seats
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 15px; color: #2C3E50; border-bottom: 2px solid #3498db; padding-bottom: 5px;'>Table {table_idx + 1}</div>", unsafe_allow_html=True)
                            
                            seat_start = table_idx * 4
                            
                            # Keep seats tight inside the table with gap="small"
                            t1, t2 = st.columns(2, gap="small")
                            with t1: render_seat_ui(f"seat_{seat_start}", st.session_state.seats.get(f"seat_{seat_start}", "Empty"), next_student, cohort, df)
                            with t2: render_seat_ui(f"seat_{seat_start+1}", st.session_state.seats.get(f"seat_{seat_start+1}", "Empty"), next_student, cohort, df)
                            
                            b1, b2 = st.columns(2, gap="small")
                            with b1: render_seat_ui(f"seat_{seat_start+2}", st.session_state.seats.get(f"seat_{seat_start+2}", "Empty"), next_student, cohort, df)
                            with b2: render_seat_ui(f"seat_{seat_start+3}", st.session_state.seats.get(f"seat_{seat_start+3}", "Empty"), next_student, cohort, df)
