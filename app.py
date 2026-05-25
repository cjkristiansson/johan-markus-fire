# --- VISNING 2: SCENARIER ---
else:
    # 1. Den usynlige knap-logik
    # Hvis "is_solo_mode" ikke findes, opretter vi den som False
    if "is_solo_mode" not in st.session_state:
        st.session_state["is_solo_mode"] = False

    # 2. Den "skjulte" knap i sidebaren (placeret så den ikke fylder eller ses)
    with st.sidebar:
        # En knap med tomt label i bunden af sidebaren
        if st.button(" ", help="System setup", type="primary"):
            st.session_state["is_solo_mode"] = not st.session_state["is_solo_mode"]
            st.rerun()

    # 3. Definer tabs
    tab_names = ["3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby"]
    if st.session_state["is_solo_mode"]: 
        tab_names.extend(["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"])
    
    tabs = st.tabs(tab_names)

    # Scenarier (Fælles)
    with tabs[0]:
        yd_35 = st.number_input("Realkreditydelse efter skat (3.5M)", value=8516, step=100, key="yd35")
        simulate_joint_fire_plan("3.5M Bolig", 3500000, 966000, 434000, yd_35, 4564, bolig_solgt=True)
    with tabs[1]:
        yd_40 = st.number_input("Realkreditydelse efter skat (4.0M)", value=4075, step=100, key="yd40")
        simulate_joint_fire_plan("4.0M Bolig", 4000000, 1846222, 1153888, yd_40, 4564, bolig_solgt=True)
    with tabs[2]:
        yd_45 = st.number_input("Realkreditydelse efter skat (4.5M)", value=4576, step=100, key="yd45")
        simulate_joint_fire_plan("4.5M Bolig", 4500000, 2250000, 1125000, yd_45, 4564, bolig_solgt=True)
    with tabs[3]:
        yd_50 = st.number_input("Realkreditydelse efter skat (5.0M)", value=6519, step=100, key="yd50")
        simulate_joint_fire_plan("5.0M Bolig", 5000000, 2408888, 983888, yd_50, 4564, bolig_solgt=True)
    with tabs[4]:
        yd_55 = st.number_input("Realkreditydelse efter skat (5.5M)", value=13659, step=100, key="yd55")
        simulate_joint_fire_plan("5.5M Bolig", 5500000, 1515000, 685000, yd_55, 4564, bolig_solgt=True)
    with tabs[5]:
        yd_vb = st.number_input("Realkreditydelse efter skat (Valby)", value=15230, step=100, key="ydvb")
        simulate_joint_fire_plan("Valby", 6700000, 0, 0, yd_vb, 4564, bolig_solgt=False)

    # Solo Scenarier (Kun synlige hvis knappen er aktiveret)
    if st.session_state["is_solo_mode"]:
        with tabs[6]:
            yd_s30 = st.number_input("Månedlig nettoydelse (Solo 3.0M)", value=7308, step=100, key="yds30")
            simulate_solo_fire_plan("3.0M Solo", 3000000, 1200000, yd_s30, 3500)
        with tabs[7]:
            yd_s35 = st.number_input("Månedlig nettoydelse (Solo 3.5M)", value=8516, step=100, key="yds35")
            simulate_solo_fire_plan("3.5M Solo", 3500000, 1400000, yd_s35, 4000)
        with tabs[8]:
            yd_s40 = st.number_input("Månedlig nettoydelse (Solo 4.0M)", value=9724, step=100, key="yds40")
            simulate_solo_fire_plan("4.0M Solo", 4000000, 1600000, yd_s40, 4500)
