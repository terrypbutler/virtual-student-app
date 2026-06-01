import streamlit as st
import pandas as pd
import random

def render_seating_plan(df):
    st.subheader("🪑 Interactive Seating Plan")
    
    # Grid settings
    rows, cols = 5, 6
    if 'seats' not in st.session_state:
        st.session_state.seats = {}

    # Sidebar controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("🪑 Planner Tools")
    if st.sidebar.button("Shuffle Randomly"):
        students = df["Full Name"].tolist()
        random.shuffle(students)
        st.session_state.seats = {f"seat_{r}_{c}": students.pop(0) if students else "Empty" 
                                  for r in range(rows) for c in range(cols)}
        st.rerun()

    # The Classroom Grid
    for r in range(rows):
        row_cols = st.columns(cols)
        for c in range(cols):
            seat_key = f"seat_{r}_{c}"
            # Default to "Empty" if seat not initialized
            current_val = st.session_state.seats.get(seat_key, "Empty")
            
            with row_cols[c]:
                new_val = st.selectbox(
                    f"R{r+1}C{c+1}", 
                    ["Empty"] + df["Full Name"].tolist(),
                    index=["Empty"] + df["Full Name"].tolist().index(current_val) 
                    if current_val in ["Empty"] + df["Full Name"].tolist() else 0,
                    key=seat_key
                )
                st.session_state.seats[seat_key] = new_val

    if st.button("Clear All"):
        st.session_state.seats = {}
        st.rerun()
