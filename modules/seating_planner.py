import streamlit as st
import pandas as pd
import random

def render_seating_plan(df):
    st.subheader("🪑 Interactive Seating Plan")
    
    rows, cols = 5, 6
    if 'seats' not in st.session_state:
        st.session_state.seats = {}

    # Get student list
    student_list = df["Full Name"].tolist()
    options = ["Empty"] + student_list

    st.sidebar.markdown("---")
    st.sidebar.subheader("🪑 Planner Tools")
    if st.sidebar.button("Shuffle Randomly"):
        students = student_list.copy()
        random.shuffle(students)
        st.session_state.seats = {f"seat_{r}_{c}": students.pop(0) if students else "Empty" 
                                  for r in range(rows) for c in range(cols)}
        st.rerun()

    for r in range(rows):
        row_cols = st.columns(cols)
        for c in range(cols):
            seat_key = f"seat_{r}_{c}"
            current_val = st.session_state.seats.get(seat_key, "Empty")
            
            # SAFE INDEX CALCULATION
            try:
                # Find the index if the student exists, otherwise default to 0 (Empty)
                idx = options.index(current_val)
            except ValueError:
                idx = 0
            
            with row_cols[c]:
                new_val = st.selectbox(
                    f"R{r+1}C{c+1}", 
                    options,
                    index=idx,
                    key=seat_key
                )
                st.session_state.seats[seat_key] = new_val

    if st.button("Clear All"):
        st.session_state.seats = {}
        st.rerun()
