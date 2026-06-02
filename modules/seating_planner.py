import streamlit as st
from modules.photo_utils import display_student_photo

def get_flexible_text(row, possible_names):
    """Helper to find columns and strip out N/A values."""
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
    st.subheader("🪑 Interactive Seating Plan")
    
    # --- PERFORMANCE FIX ---
    if len(df) > 35:
        st.warning("⚠️ **Performance Tip:** You currently have over 35 students selected. Rendering a massive photo grid makes the seating planner slow. Please use the sidebar filters to select a specific **Form Group** or **Maths Set** before assigning seats!")

    rows, cols = 5, 6
    if 'seats' not in st.session_state: st.session_state.seats = {}
    if 'selected_for_placement' not in st.session_state: st.session_state.selected_for_placement = None

    # Track who is already seated
    assigned_students = list(st.session_state.seats.values())
    ignore_list = ["N/A", "NONE", "NO", "N", "", "FALSE", "NAN", "0", "0.0"]

    # --- 1. Selection Grid (The "Photo Grid") ---
    st.markdown("### 1. Select Student to Place")
    
    # Legend for the dots
    st.caption("Key: 🔴 SEND | 🟢 EAL | 🔵 Disadvantaged (PP)")
    
    grid_cols = st.columns(8) # 8 per row
    
    for i, (_, row) in enumerate(df.iterrows()):
        name = row["Full Name"]
        
        # Check statuses for the dots
        sen_status = get_flexible_text(row, ["SEN Status", "SEND Status"]) or ""
        pp_status = get_flexible_text(row, ["Disadvantaged (PP)", "Disadvantaged", "Pupil Premium", "PP"]) or ""
        eal_status = get_flexible_text(row, ["EAL", "EAL Status"]) or ""
        
        dots = []
        if sen_status.upper() not in ignore_list: dots.append("🔴")
        if eal_status.upper() not in ignore_list: dots.append("🟢")
        if pp_status.upper() not in ignore_list: dots.append("🔵")
        dot_str = " ".join(dots)
        
        is_assigned = name in assigned_students
        is_selected = name == st.session_state.selected_for_placement
        
        with grid_cols[i % 8]:
            display_student_photo(name, cohort)
            
            # Display the dots right below the photo
            if dot_str:
                st.markdown(f"<div style='text-align: center; margin-top: 2px; margin-bottom: 5px; font-size: 14px;'>{dot_str}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='margin-bottom: 5px;'>&nbsp;</div>", unsafe_allow_html=True) # Spacer for alignment
            
            # Streamlit natively greys out and disables the button if disabled=True
            btn_label = f"✅ {name}" if is_selected else name
            if st.button(btn_label, key=f"sel_{name}", use_container_width=True, disabled=is_assigned):
                st.session_state.selected_for_placement = name
                st.rerun()

    # --- 2. Classroom Grid ---
    st.markdown("---")
    
    selected_name = st.session_state.selected_for_placement if st.session_state.selected_for_placement else "None"
    st.markdown(f"### 2. Click a seat to place: **{selected_name}**")
    
    for r in range(rows):
        row_cols = st.columns(cols)
        for c in range(cols):
            seat_key = f"seat_{r}_{c}"
            current_val = st.session_state.seats.get(seat_key, "Empty")
            
            # Highlight occupied seats in a different color
            btn_type = "primary" if current_val != "Empty" else "secondary"
            
            with row_cols[c]:
                # Button shows name of seated student
                if st.button(current_val if current_val != "Empty" else "+", key=seat_key, use_container_width=True, type=btn_type):
                    if st.session_state.selected_for_placement:
                        st.session_state.seats[seat_key] = st.session_state.selected_for_placement
                        st.session_state.selected_for_placement = None
                        st.rerun()
                    elif current_val != "Empty": 
                        # Click an already seated student to remove them from the seat
                        st.session_state.seats[seat_key] = "Empty"
                        st.rerun()

    st.write("")
    if st.button("🗑️ Clear Classroom Grid"):
        st.session_state.seats = {}
        st.session_state.selected_for_placement = None
        st.rerun()
