# ... (Keep all imports and helper functions exactly as they are) ...

def render_seating_plan(df, cohort):
    st.subheader("⚡ Visual Classroom Planner")
    
    # Initialize State
    TOTAL_SEATS = 32
    if 'seats' not in st.session_state: st.session_state.seats = {}
    if 'circulation_path' not in st.session_state: st.session_state.circulation_path = []
    # NEW: Temporary buffer for editing without re-running the grid
    if 'temp_path' not in st.session_state: st.session_state.temp_path = []
    if 'mentor_chat' not in st.session_state: st.session_state.mentor_chat = []
    
    # Configure AI
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    all_students = df["Full Name"].tolist()
    assigned_students = [s for s in st.session_state.seats.values() if s != "Empty"]
    unassigned_students = [s for s in all_students if s not in assigned_students]

    # ... (Sidebar remains exactly as it is) ...

    # --- MAIN PAGE: TOOLS & PATH TRACKER ---
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
            st.session_state.circulation_path = []
            st.session_state.temp_path = []
            st.session_state.mentor_chat = []
            st.rerun()

    # --- REPLACED: BUFFERED ROUTE BUILDER ---
    st.markdown("---")
    if assigned_students:
        st.markdown("**👣 Build Circulation Route:**")
        
        # We edit the temp_path, which doesn't trigger a rerun of the grid logic
        st.session_state.temp_path = st.multiselect(
            "Select students in order:",
            options=assigned_students,
            default=st.session_state.temp_path,
            label_visibility="collapsed"
        )
        
        # Only when this button is clicked do we update the actual path and the map colors
        if st.button("✅ Apply Route to Classroom"):
            st.session_state.circulation_path = st.session_state.temp_path
            st.rerun()
            
        if st.session_state.circulation_path:
            st.info("➔ ".join([f"**{i+1}. {name}**" for i, name in enumerate(st.session_state.circulation_path)]))
    else:
        st.caption("*Seat some students to begin building a circulation route.*")

    # ... (The rest of your code from the Front of Class Banner to the end stays exactly the same) ...
