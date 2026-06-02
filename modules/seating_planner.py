import streamlit as st
from modules.photo_utils import display_student_photo

def render_seating_plan(df, cohort):
    st.subheader("🪑 Interactive Seating Plan")
    
    rows, cols = 5, 6
    if 'seats' not in st.session_state: st.session_state.seats = {}
    if 'selected_for_placement' not in st.session_state: st.session_state.selected_for_placement = None

    # Track who is already seated to grey them out
    assigned_students = list(st.session_state.seats.values())

    # --- 1. Selection Grid (The "Photo Grid") ---
    st.markdown("### 1. Select Student to Place")
    grid_cols = st.columns(8) # 8 per row as requested
    for i, (_, row) in enumerate(df.iterrows()):
        name = row["Full Name"]
        is_assigned = name in assigned_students and name != st.session_state.selected_for_placement
        
        with grid_cols[i % 8]:
            # Apply grey filter if assigned
            opacity = 0.3 if is_assigned else 1.0
            st.markdown(f'<div style="opacity: {opacity};">', unsafe_allow_html=True)
            if st.button(name, key=f"sel_{name}", use_container_width=True):
                st.session_state.selected_for_placement = name
            display_student_photo(name, cohort)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. Classroom Grid ---
    st.markdown("---")
    st.markdown("### 2. Click a seat to place: **" + str(st.session_state.selected_for_placement) + "**")
    
    for r in range(rows):
        row_cols = st.columns(cols)
        for c in range(cols):
            seat_key = f"seat_{r}_{c}"
            current_val = st.session_state.seats.get(seat_key, "Empty")
            
            with row_cols[c]:
                # Button shows name of seated student
                if st.button(current_val if current_val != "Empty" else "+", key=seat_key, use_container_width=True):
                    if st.session_state.selected_for_placement:
                        st.session_state.seats[seat_key] = st.session_state.selected_for_placement
                        st.session_state.selected_for_placement = None
                        st.rerun()
                    elif current_val != "Empty": # Click to remove
                        st.session_state.seats[seat_key] = "Empty"
                        st.rerun()

    if st.button("Clear Classroom"):
        st.session_state.seats = {}
        st.session_state.selected_for_placement = None
        st.rerun()
