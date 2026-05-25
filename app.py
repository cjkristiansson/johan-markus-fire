# --- VISNING 2: SCENARIER (DEFAULT) ---
else:
    # Fanerne med boligplanerne sorteret fra laveste til højeste boligpris
    tab_35, tab_40, tab_45, tab_50, tab_55, tab_valby = st.tabs([
        "3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby (Nuværende)"
    ])

    with tab_35:
        # 🟢 RET DISSE TAL NÅR DU HAR BANKENS ESTIMAT
        ydelse_netto_35 = 7000
        ejerudgifter_35 = 4564
        
        simulate_joint_fire_plan("Køb af 3.5M Bolig", 3500000, 966000, 434000, ydelse_netto_35, ejerudgifter_35, bolig_solgt=True)

    with tab_40:
        # 🟢 RET DISSE TAL NÅR DU HAR BANKENS ESTIMAT
        ydelse_netto_40 = 4075
        ejerudgifter_40 = 4564
        
        simulate_joint_fire_plan("Køb af 4.0M Bolig", 4000000, 1846222, 1153888, ydelse_netto_40, ejerudgifter_40, bolig_solgt=True)

    with tab_45:
        # 🟢 RET DISSE TAL NÅR DU HAR BANKENS ESTIMAT
        ydelse_netto_45 = 4576
        ejerudgifter_45 = 4564
        
        simulate_joint_fire_plan("Køb af 4.5M Bolig", 4500000, 2250000, 1125000, ydelse_netto_45, ejerudgifter_45, bolig_solgt=True)

    with tab_50:
        # 🟢 RET DISSE TAL NÅR DU HAR BANKENS ESTIMAT
        ydelse_netto_50 = 6519
        ejerudgifter_50 = 4564
        
        simulate_joint_fire_plan("Køb af 5.0M Bolig", 5000000, 2408888, 983888, ydelse_netto_50, ejerudgifter_50, bolig_solgt=True)

    with tab_55:
        # 🟢 RET DISSE TAL NÅR DU HAR BANKENS ESTIMAT
        ydelse_netto_55 = 11000
        ejerudgifter_55 = 4564
        
        simulate_joint_fire_plan("Køb af 5.5M Bolig", 5500000, 1515000, 685000, ydelse_netto_55, ejerudgifter_55, bolig_solgt=True)

    with tab_valby:
        # Nuværende situation i Valby
        ydelse_netto_valby = 15230
        ejerudgifter_valby = 4564
        
        simulate_joint_fire_plan("Valby (Nuværende)", 6700000, 0, 0, ydelse_netto_valby, ejerudgifter_valby, bolig_solgt=False)
