import streamlit as st

def render_seating_plan(df):
    """
    Renders a classroom grid where a user selects a student from a top-level 
    dropdown and clicks a seat to assign them.
    """
    st.subheader("🪑 Interactive Seating Plan")
    
    # Define classroom dimensions
    rows, cols = 5, 6
    
    # Initialize session state for seats if they don't exist
    if 'seats' not in st.session_state:
        st.session_state.seats = {}

    # Define the student list from the passed dataframe
    student_list = df["Full Name"].tolist()
    options = ["Empty"] + student_list

    # --- Top-level selection UI ---
    st.markdown("### 1. Select Student")
    col_a, col_b = st.columns([3, 1])
    
    with col_a:
        # This dropdown acts as your 'stamp' tool
        student_to_place = st.selectbox("Select student to place in a seat:", options)
    
    with col_b:
        st.write("") # Spacer to align with dropdown
        st.write("")
        if st.button("Clear All Seats", use_container_width=True):
            st.session_state.seats = {}
            st.rerun()

    st.markdown("---")
    st.markdown("### 2. Click a seat to assign the selected student")

    # --- The Classroom Grid ---
    # We loop through rows and columns to generate the grid
    for r in range(rows):
        row_cols = st.columns(cols)
        for c in range(cols):
            seat_key = f"seat_{r}_{c}"
            
            # Get the current student in this specific seat, default to "Empty"
            current_val = st.session_state.seats.get(seat_key, "Empty")
            
            # Styling: Use a different color if seat is occupied vs empty
            btn_type = "primary" if current_val != "Empty" else "secondary"
            
            with row_cols[c]:
                # The seat button: Clicking it assigns the student selected in the dropdown
                if st.button(current_val, key=seat_key, use_container_width=True, type=btn_type):
                    if student_to_place != "Empty":
                        st.session_state.seats[seat_key] = student_to_place
                        st.rerun()
                    else:
                        # Clicking an occupied seat with "Empty" selected clears that seat
                        st.session_state.seats[seat_key] = "Empty"
                        st.rerun()
