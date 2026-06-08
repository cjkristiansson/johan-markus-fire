import streamlit as st
import pandas as pd
import numpy as np

# Konfiguration
st.set_page_config(page_title="FIRE Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- INDLÆS EKSTERN CSS ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css("style.css")

# --- INITIALISERING AF SESSION STATE (BASISDATA) ---
if "inkomst_j" not in st.session_state: st.session_state["inkomst_j"] = 38468
if "inkomst_m" not in st.session_state: st.session_state["inkomst_m"] = 32983
if "pension_j" not in st.session_state: st.session_state["pension_j"] = 845000
if "pension_m" not in st.session_state: st.session_state["pension_m"] = 570000
if "pension_indb_j" not in st.session_state: st.session_state["pension_indb_j"] = 6500
if "pension_indb_m" not in st.session_state: st.session_state["pension_indb_m"] = 5000

# Formue før boligkøb
if "cash_j_base" not in st.session_state: st.session_state["cash_j_base"] = 2567500
if "cash_m_base" not in st.session_state: st.session_state["cash_m_base"] = 1153888
if "basis_ask_j" not in st.session_state: st.session_state["basis_ask_j"] = 174000
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 65000
if "basis_ask_m" not in st.session_state: st.session_state["basis_ask_m"] = 170000
if "basis_frie_m" not in st.session_state: st.session_state["basis_frie_m"] = 0

# Toggles og Fælles Madbudget variabler
if "use_bsu_m" not in st.session_state: st.session_state["use_bsu_m"] = False
if "use_loensikring_j" not in st.session_state: st.session_state["use_loensikring_j"] = False
if "use_loensikring_m" not in st.session_state: st.session_state["use_loensikring_m"] = False
if "use_real_drawdown" not in st.session_state: st.session_state["use_real_drawdown"] = False
if "use_ask_500k" not in st.session_state: st.session_state["use_ask_500k"] = False
if "mad_total_val" not in st.session_state: st.session_state["mad_total_val"] = 6000
if "mad_j_val" not in st.session_state: st.session_state["mad_j_val"] = 4500
if "mc_active" not in st.session_state: st.session_state["mc_active"] = False

# Personlige budgetter
if "budget_j" not in st.session_state:
    st.session_state["budget_j"] = {"Studielaan": 0, "Mad": st.session_state["mad_j_val"], "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 0, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
if "budget_m" not in st.session_state:
    st.session_state["budget_m"] = {"Studielaan": 1600, "Mad": st.session_state["mad_total_val"] - st.session_state["mad_j_val"], "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 0, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

# --- POP-UP MODAL TIL REGLER OG LOGIK ---
@st.dialog("📜 Modellens Regler & Logik")
def show_rules_dialog():
    st.markdown("""
    * **Trin 0 (Boligkøb først):** Startdepotet i år 1 er formuen *efter* udbetaling til bolig.
    * **Lagerbeskatning:** Frie midler beskattes progressivt (27/42%). Progressionsgrænsen indekseres årligt. ASK-loftet udnyttes før indskud på frie midler.
    * **Udskudt Salg (Fase 1 & 2):** Hvis salget udskydes, låses friværdien. Modellen fremskriver asymmetrisk boliginflation og faste afdrag (84.000/år) frem til Salgsåret.
    * **Monte Carlo Simulering:** Når aktiveret, kører modellen 1.000 parallelle universer vektoriseret i NumPy baseret på historisk volatilitet for at stressteste Barista-tilværelsen.
    """)

# --- TOP HEADER ---
col_title, col_link = st.columns([0.85, 0.15], vertical_alignment="center")
with col_title:
    st.markdown("<h1 style='margin-top: -15px; margin-bottom: 0px;'>FIRE Brofinansiering</h1>", unsafe_allow_html=True)
with col_link:
    if st.button("📜 Regler & Logik", type="tertiary", use_container_width=True):
        show_rules_dialog()

# --- HOVEDNAVIGATION (PILLS) ---
view_selection = st.pills("Navigation", options=["Boligscenarier", "⚙️ Basisdata & Opsætning"], default="Boligscenarier", label_visibility="collapsed")
st.write("") 

# --- SIDEBAR ---
st.sidebar.header("Globale Antagelser")

if "active_preset" not in st.session_state:
    st.session_state["active_preset"] = "Realistisk"
    st.session_state["slider_return"] = 7.0
    st.session_state["slider_drawdown"] = 3.5
    st.session_state["slider_inflation"] = 2.0

def set_preset(preset):
    st.session_state["active_preset"] = preset
    st.session_state["mc_active"] = False
    if preset == "Standard":
        st.session_state["slider_return"] = 7.0
        st.session_state["slider_drawdown"] = 4.5
        st.session_state["slider_inflation"] = 2.0
    elif preset == "Realistisk":
        st.session_state["slider_return"] = 7.0
        st.session_state["slider_drawdown"] = 3.5
        st.session_state["slider_inflation"] = 2.0
    elif preset == "Konservativ":
        st.session_state["slider_return"] = 5.5
        st.session_state["slider_drawdown"] = 3.5
        st.session_state["slider_inflation"] = 2.5

def clear_preset():
    st.session_state["active_preset"] = "Custom"
    st.session_state["mc_active"] = False

def trigger_mc():
    st.session_state["mc_active"] = True

# Vertikalt stablede knapper
st.sidebar.button("Standard", type="primary" if st.session_state["active_preset"] == "Standard" else "secondary", use_container_width=True, on_click=set_preset, args=("Standard",))
st.sidebar.button("Realistisk", type="primary" if st.session_state["active_preset"] == "Realistisk" else "secondary", use_container_width=True, on_click=set_preset, args=("Realistisk",))
st.sidebar.button("Konservativ", type="primary" if st.session_state["active_preset"] == "Konservativ" else "secondary", use_container_width=True, on_click=set_preset, args=("Konservativ",))

global_return_rate_gross = st.sidebar.slider("Bruttoafkast under opsparing (%)", min_value=3.0, max_value=10.0, step=0.5, on_change=clear_preset, key="slider_return") / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast i passiv fase (%)", min_value=2.0, max_value=8.0, step=0.1, on_change=clear_preset, key="slider_drawdown") / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", min_value=0.0, max_value=5.0, step=0.5, on_change=clear_preset, key="slider_inflation") / 100

st.sidebar.toggle("Købekraftsjusteret udtræk i FIRE-fasen", key="use_real_drawdown", on_change=clear_preset)
st.sidebar.toggle("Hæv ASK-loft til 500.000 kr.", key="use_ask_500k", on_change=clear_preset)

st.sidebar.divider()
st.sidebar.markdown("### 🏡 Salg af Valby-lejlighed (Fase 1)")
global_salgsaar = st.sidebar.slider("Salgsår (0 = Sælg nu)", min_value=0, max_value=10, value=0, step=1, on_change=clear_preset)
global_bolig_inflation = st.sidebar.slider("Årlig boligprisstigning (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.5, on_change=clear_preset) / 100

st.sidebar.divider()
st.sidebar.markdown("### 🎲 Monte Carlo Simulering")
mc_volatility = st.sidebar.slider("Markedsvolatilitet (%)", min_value=5.0, max_value=25.0, value=15.0, step=1.0, on_change=clear_preset) / 100
st.sidebar.button("Beregn Monte Carlo (1000 kørsler)", type="primary", use_container_width=True, on_click=trigger_mc)

st.sidebar.divider()
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5, on_change=clear_preset)
pensionsalder_j = st.sidebar.number_input("Johans pensionsalder", min_value=55, max_value=75, value=67, step=1, on_change=clear_preset)
pensionsalder_m = st.sidebar.number_input("Markus' pensionsalder", min_value=55, max_value=75, value=65, step=1, on_change=clear_preset)

st.sidebar.divider()
st.sidebar.text_input("Gendan Scenarie-ID", help="Indtast ID for at indlæse specifik konfiguration.", key="secret_id")

# --- DYNAMISKE SIMULERINGSFUNKTIONER ---
def calculate_drawdown_monthly_income(depot_total_arr, current_age, target_age, net_return_rate, inflation_rate, use_real_rate):
    if current_age >= target_age: return depot_total_arr * 0.0
    years_left = target_age - current_age
    months_left = years_left * 12
    
    if use_real_rate:
        effective_rate = ((1 + net_return_rate) / (1 + inflation_rate)) - 1
    else:
        effective_rate = net_return_rate
        
    monthly_rate = effective_rate / 12
    if monthly_rate <= 0: return depot_total_arr / months_left
    return depot_total_arr * (monthly_rate * (1 + monthly_rate)**months_left) / ((1 + monthly_rate)**months_left - 1)

def get_emoji_status(barista_hours):
    if barista_hours <= 0: return "🏁 0.0t"
    elif 0 < barista_hours <= 15: return f"🟡 {barista_hours:.1f}t"
    elif 15 < barista_hours <= 25: return f"🟠 {barista_hours:.1f}t"
    else: return f"🔴 {barista_hours:.1f}t"

def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, ydelse_default, ydelse_key, ejerudgifter_total, bolig_solgt, boligskat_md):
    pal_tax, weeks_per_month, age_j, age_m = 0.153, 4.33, 41, 32
    
    ydelse_key_clean = ydelse_key.replace("solo_", "")
    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key_clean}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key_clean}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{ydelse_key_clean}", 4.0) / 100
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{ydelse_key_clean}", False)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key_clean}", 50000)
    use_real_drawdown = st.session_state.get("use_real_drawdown", False)
    use_ask_500k = st.session_state.get("use_ask_500k", False)
    ask_base_limit = 500000 if use_ask_500k else 174000

    # MC Logik
    is_mc = st.session_state.get("mc_active", False)
    n_sims = 1000 if is_mc else 1
    vol = mc_volatility if is_mc else 0.0
    market_returns = np.random.normal(loc=global_return_rate_gross, scale=vol, size=(26, n_sims))

    # Fase 1: Håndter udskudt salg. 
    is_valby = "Valby" in scenario_name
    actual_salgsaar = 0 if is_valby else global_salgsaar
    
    valby_pris = 6700000
    maal_pris = boligpris

    use_bsu = st.session_state.get("use_bsu_m", False)
    bsu_amount = 292060
    
    cash_j = st.session_state["cash_j_base"] if bolig_solgt else 0
    cash_m = st.session_state["cash_m_base"] if bolig_solgt else 0
    
    if actual_salgsaar == 0:
        if use_bsu and bolig_solgt:
            cash_m += bsu_amount
            udbetaling_j -= (bsu_amount / 2) 
            udbetaling_m += (bsu_amount / 2)
            bsu_passive = 0
        else:
            bsu_passive = 983
            
        mangler_m = max(0, udbetaling_m - cash_m)
        faktisk_udbetaling_m = udbetaling_m - mangler_m
        udbetaling_j_total = udbetaling_j + mangler_m
        faktisk_udbetaling_j = udbetaling_j_total - max(0, udbetaling_j_total - cash_j)

        if max(0, udbetaling_j_total - cash_j) > 0 and n_sims == 1:
            st.error(f"⚠️ ADVARSEL: Udbetalingen overstiger jeres likviditet.")

        base_frie_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        base_frie_m = st.session_state["basis_frie_m"] + (cash_m - faktisk_udbetaling_m)
        
        bolig_faelles_current = (ydelse_default + ejerudgifter_total + boligskat_md) / 2
        restgaeld_start = boligpris - (faktisk_udbetaling_j + faktisk_udbetaling_m)
        
        locked_frivaerdi_j = 0.0
        locked_frivaerdi_m = 0.0
    else:
        bsu_passive = 983 if use_bsu else 983
        faktisk_udbetaling_j = 0
        faktisk_udbetaling_m = 0
        
        base_frie_j = st.session_state["basis_frie_j"]
        base_frie_m = st.session_state["basis_frie_m"]
        
        valby_ydelse = 15230
        valby_ejerudgifter = 4564
        valby_boligskat = 0
        bolig_faelles_current = (valby_ydelse + valby_ejerudgifter + valby_boligskat) / 2
        restgaeld_start = 0 
        
        locked_frivaerdi_j = float(cash_j)
        locked_frivaerdi_m = float(cash_m)

    depot_free_j = np.full(n_sims, base_frie_j, dtype=float)
    depot_free_m = np.full(n_sims, base_frie_m, dtype=float)
    depot_ask_j = np.full(n_sims, st.session_state["basis_ask_j"], dtype=float)
    depot_ask_m = np.full(n_sims, st.session_state["basis_ask_m"], dtype=float)
    pension_j_current = np.full(n_sims, st.session_state["pension_j"], dtype=float)
    pension_m_current = np.full(n_sims, st.session_state["pension_m"], dtype=float)

    j_reached_arr = np.zeros(n_sims, dtype=bool)
    m_reached_arr = np.zeros(n_sims, dtype=bool)

    target_total_udb = udbetaling_j + udbetaling_m
    ui_cash_pct = (target_total_udb / boligpris * 100) if boligpris > 0 else 0
    ui_loan_pct = 100 - ui_cash_pct

    space_j_init = np.maximum(0, ask_base_limit - depot_ask_j)
    move_j = np.minimum(space_j_init, np.maximum(0, depot_free_j))
    depot_ask_j += move_j
    depot_free_j -= move_j

    space_m_init = np.maximum(0, ask_base_limit - depot_ask_m)
    move_m = np.minimum(space_m_init, np.maximum(0, depot_free_m))
    depot_ask_m += move_m
    depot_free_m -= move_m

    with st.expander("🏠 Vis økonomiske detaljer & lån", expanded=False):
        if actual_salgsaar > 0:
            st.info(f"⏳ **Salg udskudt til År {actual_salgsaar}.** Jeres nuværende Valby-friværdi er låst i mursten indtil da. De viste tal nedenfor (startdepot og boliglån) afspejler jeres ønskede målbolig og jeres nuværende frie likviditet i År 0.")
            
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        with col_inp:
            st.markdown(
                f"<p style='margin-bottom: 60px; margin-top: 0; line-height: 1.3;'>"
                f"Mål: {int(ui_cash_pct)}% kontantudbetaling ({f'{int(target_total_udb):,}'.replace(',', '.')} kr.) | {int(ui_loan_pct)}% lån</p>", 
                unsafe_allow_html=True
            )
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key, on_change=clear_preset)

        if actual_salgsaar == 0:
            bolig_faelles_current = (realkreditydelse_netto + ejerudgifter_total + boligskat_md) / 2

        budget_j_total = sum(st.session_state["budget_j"].values())
        budget_m_total = sum(st.session_state["budget_m"].values())

        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_faelles_current)
        start_inv_md_m = st.session_state["inkomst_m"] - (budget_m_total + bolig_faelles_current) + bsu_passive
        
        start_fire_j = sum(v for k, v in st.session_state["budget_j"].items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_faelles_current
        start_fire_m = sum(v for k, v in st.session_state["budget_m"].items() if k not in ["A_kasse_Fagforening", "Loensikring", "Studielaan"]) + bolig_faelles_current

        skat_line_j = f"**Boligskat (egen andel):** {f'{int(boligskat_md / 2):,}'.replace(',', '.')} kr./md. " if boligskat_md > 0 and actual_salgsaar == 0 else ""
        skat_line_m = f"**Boligskat (egen andel):** {f'{int(boligskat_md / 2):,}'.replace(',', '.')} kr./md. " if boligskat_md > 0 and actual_salgsaar == 0 else ""

        with col_j:
            st.subheader(f"JOHAN")
            st.markdown(f"""
            **Mål-Udbetaling:** {f'{int(udbetaling_j):,}'.replace(',', '.')} kr.  
            **Mål-Realkreditydelse:** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.  
            {skat_line_j}**Startdepot (År 0):** {f'{int(depot_free_j[0] + depot_ask_j[0]):,}'.replace(',', '.')} kr.  
            **Mdl. opsparing (År 0):** {f'{int(start_inv_md_j):,}'.replace(',', '.')} kr.  
            **Mdl. Udgifter (År 0):** {f'{int(start_fire_j):,}'.replace(',', '.')} kr./md.
            """)
        
        with col_m:
            st.subheader(f"MARKUS")
            st.markdown(f"""
            **Mål-Udbetaling:** {f'{int(udbetaling_m):,}'.replace(',', '.')} kr.  
            **Mål-Realkreditydelse:** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.  
            {skat_line_m}**Startdepot (År 0):** {f'{int(depot_free_m[0] + depot_ask_m[0]):,}'.replace(',', '.')} kr.  
            **Mdl. opsparing (År 0):** {f'{int(start_inv_md_m):,}'.replace(',', '.')} kr.  
            **Mdl. Udgifter (År 0):** {f'{int(start_fire_m):,}'.replace(',', '.')} kr./md.
            """)

    if "Valby" in scenario_name:
        oprindelig_rente_mnd = 0.024 / 12
        start_afdrag_mnd = 6929
    else:
        oprindelig_rente_mnd = 0.04 / 12

    # --- UI For Monte Carlo Toggle ---
    if is_mc:
        st.write("")
        with st.expander("❓ Sådan læser du Monte Carlo-resultaterne", expanded=False):
            st.markdown("""
            **Median (Det Forventede):** Det midterste udfald af de 1.000 simulerede markedsforløb. Dette er jeres 50/50 sandsynlighed og lægger sig meget op ad den klassiske, lineære model.
            
            **P10 (Worst-Case Formue & Indkomst):** Den 10. percentil. Ud af 1.000 simulerede virkeligheder er dette det 100. dårligste. Det betyder, at I med 90 % statistisk sikkerhed vil have *flere* penge end dette, selv hvis markedet underpræsterer massivt i de tidlige år.
            
            **P90 (Worst-Case Arbejdstid):** Den 90. percentil. Da lavere er bedre for arbejdstimer, viser dette tal det maksimale antal timer, I risikerer at skulle arbejde for at klare regningerne under en kriselignende recession.
            
            **Succesrate:** Procentdelen af de 1.000 universer, hvor depotet i det pågældende år kan dække alle udgifter, så I kan trække jer fuldstændig tilbage (0.0 barista-timer).
            """)
            
        mc_view = st.segmented_control(
            "Vælg visning",
            options=["Median (Forventet scenarie)", "P10 (Worst-case scenarie)"],
            default="Median (Forventet scenarie)",
            key=f"mc_view_joint_{ydelse_key_clean}",
            label_visibility="collapsed"
        )
        is_worst_case = (mc_view == "P10 (Worst-case scenarie)")
    else:
        is_worst_case = False

    table_data = []
    
    for year in range(0, 26):
        c_age_j, c_age_m = age_j + year, age_m + year
        current_ret = market_returns[year]
        
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > actual_salgsaar:
            mdr_gaaet = (oml_aar - actual_salgsaar) * 12
            if "Valby" in scenario_name:
                afdraget_beloeb = start_afdrag_mnd * (((1 + oprindelig_rente_mnd)**mdr_gaaet - 1) / oprindelig_rente_mnd)
                restgaeld_ved_oml = max(0, restgaeld_start - afdraget_beloeb)
            else:
                restgaeld_ved_oml = restgaeld_start * ((1 + oprindelig_rente_mnd)**360 - (1 + oprindelig_rente_mnd)**mdr_gaaet) / ((1 + oprindelig_rente_mnd)**360 - 1)
            
            ny_hovedstol = restgaeld_ved_oml + oml_omk
            mnd_rente_ny = oml_rente / 12
            
            if not oml_afdrag_fri:
                ny_lån_ydelse = ny_hovedstol * (mnd_rente_ny * (1 + mnd_rente_ny)**360) / ((1 + mnd_rente_ny)**360 - 1)
            else:
                ny_lån_ydelse = ny_hovedstol * mnd_rente_ny
                
            renter_md = (ny_hovedstol * oml_rente) / 12
            netto_bolig_faelles = (ny_lån_ydelse + ejerudgifter_total + boligskat_md - (renter_md * 0.256)) / 2
            
            diff_faelles = bolig_faelles_current - netto_bolig_faelles
            start_fire_j -= diff_faelles; start_fire_m -= diff_faelles
            start_inv_md_j += diff_faelles; start_inv_md_m += diff_faelles
            bolig_faelles_current = netto_bolig_faelles

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate); start_fire_m *= (1 + global_inflation_rate)
            
            if actual_salgsaar > 0 and year <= actual_salgsaar:
                valby_pris_stigning = valby_pris * global_bolig_inflation
                maal_pris_stigning = maal_pris * global_bolig_inflation
                asymmetrisk_gevinst = valby_pris_stigning - maal_pris_stigning
                
                valby_pris += valby_pris_stigning
                maal_pris += maal_pris_stigning
                
                locked_frivaerdi_j += 42000 + (asymmetrisk_gevinst / 2)
                locked_frivaerdi_m += 42000 + (asymmetrisk_gevinst / 2)
                
                if year == actual_salgsaar:
                    skaleret_udbetaling_j = udbetaling_j * (maal_pris / boligpris)
                    skaleret_udbetaling_m = udbetaling_m * (maal_pris / boligpris)
                    
                    if use_bsu:
                        locked_frivaerdi_m += bsu_amount
                        skaleret_udbetaling_j -= (bsu_amount / 2)
                        skaleret_udbetaling_m += (bsu_amount / 2)
                        bsu_passive = 0
                        start_inv_md_m -= 983
                        
                    mangler_m = max(0, skaleret_udbetaling_m - locked_frivaerdi_m)
                    fakt_udb_m = skaleret_udbetaling_m - mangler_m
                    udb_j_tot = skaleret_udbetaling_j + mangler_m
                    fakt_udb_j = udb_j_tot - max(0, udb_j_tot - locked_frivaerdi_j)
                    
                    if fakt_udb_j > locked_frivaerdi_j and n_sims == 1:
                        st.error(f"⚠️ I År {year} overstiger den fremskrevne udbetaling friværdien i {scenario_name} scenariet.")
                    
                    depot_free_j += max(0, locked_frivaerdi_j - fakt_udb_j)
                    depot_free_m += max(0, locked_frivaerdi_m - fakt_udb_m)
                    
                    ny_ydelse = realkreditydelse_netto * (maal_pris / boligpris)
                    ny_ejerudgifter = ejerudgifter_total * ((1 + global_inflation_rate)**year)
                    ny_boligskat = boligskat_md * ((1 + global_inflation_rate)**year)
                    ny_bolig_faelles = (ny_ydelse + ny_ejerudgifter + ny_boligskat) / 2
                    
                    valby_faelles_nu = bolig_faelles_current * ((1 + global_inflation_rate)**year)
                    diff_faelles = valby_faelles_nu - ny_bolig_faelles
                    
                    start_fire_j -= diff_faelles
                    start_fire_m -= diff_faelles
                    
                    diff_faelles_base = diff_faelles / ((1 + global_inflation_rate)**year)
                    start_inv_md_j += diff_faelles_base
                    start_inv_md_m += diff_faelles_base
                    
                    bolig_faelles_current = ny_bolig_faelles / ((1 + global_inflation_rate)**year)
                    restgaeld_start = maal_pris - (fakt_udb_j + fakt_udb_m)

            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            prog_limit_m = 79400 * ((1 + global_inflation_rate)**year)
            
            return_frie_j = depot_free_j * current_ret
            return_frie_m = depot_free_m * current_ret
            
            tax_j = np.where(return_frie_j <= prog_limit_j, return_frie_j * 0.27, prog_limit_j * 0.27 + (return_frie_j - prog_limit_j) * 0.42)
            tax_m = np.where(return_frie_m <= prog_limit_m, return_frie_m * 0.27, prog_limit_m * 0.27 + (return_frie_m - prog_limit_m) * 0.42)
            
            depot_free_j = np.maximum(0, depot_free_j + (return_frie_j - tax_j))
            depot_free_m = np.maximum(0, depot_free_m + (return_frie_m - tax_m))
            
            depot_ask_j = np.maximum(0, depot_ask_j * (1 + current_ret * 0.83))
            depot_ask_m = np.maximum(0, depot_ask_m * (1 + current_ret * 0.83))
            
            depot_free_j += np.where(~j_reached_arr, start_inv_md_j * 12 * ((1 + global_inflation_rate)**year), 0)
            depot_free_m += np.where(~m_reached_arr, start_inv_md_m * 12 * ((1 + global_inflation_rate)**year), 0)

            ask_limit_year = ask_base_limit * ((1 + global_inflation_rate)**year)
            space_j = np.maximum(0, ask_limit_year - depot_ask_j)
            move_j = np.minimum(space_j, np.maximum(0, depot_free_j))
            depot_ask_j += move_j
            depot_free_j -= move_j

            space_m = np.maximum(0, ask_limit_year - depot_ask_m)
            move_m = np.minimum(space_m, np.maximum(0, depot_free_m))
            depot_ask_m += move_m
            depot_free_m -= move_m

            pension_j_current = np.maximum(0, pension_j_current * (1 + (current_ret * (1 - pal_tax))))
            pension_m_current = np.maximum(0, pension_m_current * (1 + (current_ret * (1 - pal_tax))))
            pension_j_current += np.where(~j_reached_arr, st.session_state["pension_indb_j"] * 12 * ((1 + global_inflation_rate)**year), 0)
            pension_m_current += np.where(~m_reached_arr, st.session_state["pension_indb_m"] * 12 * ((1 + global_inflation_rate)**year), 0)

        p_j = calculate_drawdown_monthly_income(np.maximum(0, depot_ask_j + depot_free_j), c_age_j, pensionsalder_j, global_return_rate_net_drawdown, global_inflation_rate, use_real_drawdown)
        p_m_drawdown = calculate_drawdown_monthly_income(np.maximum(0, depot_ask_m + depot_free_m), c_age_m, pensionsalder_m, global_return_rate_net_drawdown, global_inflation_rate, use_real_drawdown)
        p_m_total = p_m_drawdown + bsu_passive

        h_j_array = np.maximum(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)
        h_m_array = np.maximum(0, start_fire_m - p_m_total) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        j_reached_arr = j_reached_arr | (h_j_array <= 0)
        m_reached_arr = m_reached_arr | (h_m_array <= 0)

        if n_sims > 1:
            med_dep_j = np.median(depot_ask_j + depot_free_j)
            p10_dep_j = np.percentile(depot_ask_j + depot_free_j, 10)
            med_p_j = np.median(p_j)
            p10_p_j = np.percentile(p_j, 10)
            med_h_j = np.median(h_j_array)
            p90_h_j = np.percentile(h_j_array, 90)
            succ_j = np.mean(h_j_array <= 0) * 100

            med_dep_m = np.median(depot_ask_m + depot_free_m)
            p10_dep_m = np.percentile(depot_ask_m + depot_free_m, 10)
            med_p_m = np.median(p_m_total)
            p10_p_m = np.percentile(p_m_total, 10)
            med_h_m = np.median(h_m_array)
            p90_h_m = np.percentile(h_m_array, 90)
            succ_m = np.mean(h_m_array <= 0) * 100

            if is_worst_case:
                table_data.append({
                    "År": year, "J.alder": c_age_j, 
                    "J.depot (M)": f"{p10_dep_j/1e6:.2f}", 
                    "J.Passiv (kr)": f"{int(p10_p_j):,}".replace(',', '.'), 
                    "J.Arbtid": f"{get_emoji_status(p90_h_j).split()[0]} {p90_h_j:.1f}t",
                    "J.Succes": f"{succ_j:.0f}%",
                    "M.alder": c_age_m, 
                    "M.depot (M)": f"{p10_dep_m/1e6:.2f}", 
                    "M.Passiv (kr)": f"{int(p10_p_m):,}".replace(',', '.'), 
                    "M.Arbtid": f"{get_emoji_status(p90_h_m).split()[0]} {p90_h_m:.1f}t",
                    "M.Succes": f"{succ_m:.0f}%"
                })
            else:
                table_data.append({
                    "År": year, "J.alder": c_age_j, 
                    "J.depot (M)": f"{med_dep_j/1e6:.2f}", 
                    "J.Passiv (kr)": f"{int(med_p_j):,}".replace(',', '.'), 
                    "J.Arbtid": get_emoji_status(med_h_j),
                    "J.Succes": f"{succ_j:.0f}%",
                    "M.alder": c_age_m, 
                    "M.depot (M)": f"{med_dep_m/1e6:.2f}", 
                    "M.Passiv (kr)": f"{int(med_p_m):,}".replace(',', '.'), 
                    "M.Arbtid": get_emoji_status(med_h_m),
                    "M.Succes": f"{succ_m:.0f}%"
                })
        else:
            table_data.append({
                "År": year, "J.alder": c_age_j, 
                "J.depot (M)": f"{(depot_ask_j[0] + depot_free_j[0])/1e6:.2f}", 
                "J.Passiv (kr)": f"{int(p_j[0]):,}".replace(',', '.'), 
                "J.Arbtid": get_emoji_status(h_j_array[0]), 
                "M.alder": c_age_m, 
                "M.depot (M)": f"{(depot_ask_m[0] + depot_free_m[0])/1e6:.2f}", 
                "M.Passiv (kr)": f"{int(p_m_total[0]):,}".replace(',', '.'), 
                "M.Arbtid": get_emoji_status(h_m_array[0])
            })
            if j_reached_arr[0] and m_reached_arr[0]: break

    st.table(pd.DataFrame(table_data).set_index("År"))
    
    with st.expander("🔄 Omlægningsscenarie", expanded=False):
        st.toggle("Aktiver omlægningsscenarie", value=False, key=f"aktiver_oml_{ydelse_key_clean}", on_change=clear_preset)
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        col_o1.number_input("År for omlægning (0-10)", min_value=0, max_value=10, value=5, key=f"oml_aar_{ydelse_key_clean}", on_change=clear_preset)
        col_o2.number_input("Ny rente + bidrag (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1, key=f"oml_rente_{ydelse_key_clean}", on_change=clear_preset)
        col_o3.toggle("Afdragsfrihed aktiveret", value=False, key=f"oml_afdrag_fri_{ydelse_key_clean}", on_change=clear_preset)
        col_o4.number_input("Omkostninger (kr)", value=50000, step=5000, key=f"oml_omk_{ydelse_key_clean}", on_change=clear_preset)

def simulate_solo_fire_plan(scenario_name, boligpris, udbetaling_j, ydelse_default, ydelse_key, ejerudgifter_total, boligskat_md):
    pal_tax, weeks_per_month, age_j = 0.153, 4.33, 41
    
    s_key = f"solo_{ydelse_key}"
    ydelse_key_clean = s_key.replace("solo_", "")
    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key_clean}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key_clean}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{ydelse_key_clean}", 4.0) / 100
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{ydelse_key_clean}", False)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key_clean}", 50000)
    use_real_drawdown = st.session_state.get("use_real_drawdown", False)
    use_ask_500k = st.session_state.get("use_ask_500k", False)
    ask_base_limit = 500000 if use_ask_500k else 174000

    is_mc = st.session_state.get("mc_active", False)
    n_sims = 1000 if is_mc else 1
    vol = mc_volatility if is_mc else 0.0
    market_returns = np.random.normal(loc=global_return_rate_gross, scale=vol, size=(26, n_sims))

    cash_j = st.session_state["cash_j_base"]
    faktisk_udbetaling_j = min(udbetaling_j, cash_j)
    cash_pct = (faktisk_udbetaling_j / boligpris * 100) if boligpris > 0 else 0
    loan_pct = 100 - cash_pct

    is_valby = "Valby" in scenario_name
    actual_salgsaar = 0 if is_valby else global_salgsaar
    valby_pris = 6700000
    maal_pris = boligpris

    if actual_salgsaar == 0:
        base_frie_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        bolig_total_current = ydelse_default + ejerudgifter_total + boligskat_md
        restgaeld_start = boligpris - faktisk_udbetaling_j
        locked_frivaerdi_j = 0.0
    else:
        faktisk_udbetaling_j = 0
        base_frie_j = st.session_state["basis_frie_j"]
        valby_ydelse = 15230
        valby_ejerudgifter = 4564
        valby_boligskat = 0
        bolig_total_current = valby_ydelse + valby_ejerudgifter + valby_boligskat
        restgaeld_start = 0
        locked_frivaerdi_j = float(cash_j)

    depot_free_j = np.full(n_sims, base_frie_j, dtype=float)
    depot_ask_j = np.full(n_sims, st.session_state["basis_ask_j"], dtype=float)
    pension_j_current = np.full(n_sims, st.session_state["pension_j"], dtype=float)
    j_reached_arr = np.zeros(n_sims, dtype=bool)

    space_j_init = np.maximum(0, ask_base_limit - depot_ask_j)
    move_j = np.minimum(space_j_init, np.maximum(0, depot_free_j))
    depot_ask_j += move_j
    depot_free_j -= move_j

    with st.expander("⚙️ Vis økonomiske detaljer & lån", expanded=False):
        if actual_salgsaar > 0:
            st.info(f"⏳ **Salg udskudt til År {actual_salgsaar}.** Jeres nuværende Valby-friværdi er låst i mursten indtil da. De viste tal nedenfor (startdepot og boliglån) afspejler den ønskede målbolig og din nuværende frie likviditet i År 0.")
            
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        with col_inp:
            st.markdown(
                f"<p style='margin-bottom: 105px; margin-top: 0; line-height: 1.3;'>"
                f"{int(cash_pct)}% kontantudbetaling ({f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.) | {int(loan_pct)}% lån</p>", 
                unsafe_allow_html=True
            )
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key, on_change=clear_preset)

        if actual_salgsaar == 0:
            bolig_total_current = realkreditydelse_netto + ejerudgifter_total + boligskat_md

        solo_budget_j = st.session_state["budget_j"].copy()
        solo_budget_j["Mad"] = 3000

        budget_j_total = sum(solo_budget_j.values())
        
        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_total_current)
        start_fire_j = sum(v for k, v in solo_budget_j.items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_total_current

        with col_j:
            st.subheader(f"JOHAN (SOLO)")
            st.markdown(f"""
            **Boligpris:** {f'{int(boligpris):,}'.replace(',', '.')} kr.  
            **Mål-Udbetaling:** {f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.  
            **Boligudgifter total:** {f'{int(bolig_total_current):,}'.replace(',', '.')} kr./md.  
            **Startdepot (År 0):** {f'{int(depot_free_j[0] + depot_ask_j[0]):,}'.replace(',', '.')} kr.  
            **Mdl. opsparing:** {f'{int(start_inv_md_j):,}'.replace(',', '.')} kr.  
            **Mdl. Udgifter:** {f'{int(start_fire_j):,}'.replace(',', '.')} kr./md.
            """)
            
    st.write("")

    if "Valby" in scenario_name:
        oprindelig_rente_mnd = 0.024 / 12
        start_afdrag_mnd = 6929
    else:
        oprindelig_rente_mnd = 0.04 / 12

    # --- UI For Monte Carlo Toggle ---
    if is_mc:
        st.write("")
        with st.expander("❓ Sådan læser du Monte Carlo-resultaterne", expanded=False):
            st.markdown("""
            **Median (Det Forventede):** Det midterste udfald af de 1.000 simulerede markedsforløb. Dette er din 50/50 sandsynlighed og lægger sig meget op ad den klassiske, lineære model.
            
            **P10 (Worst-Case Formue & Indkomst):** Den 10. percentil. Ud af 1.000 simulerede virkeligheder er dette det 100. dårligste. Det betyder, at du med 90 % statistisk sikkerhed vil have *flere* penge end dette, selv hvis markedet underpræsterer massivt.
            
            **P90 (Worst-Case Arbejdstid):** Den 90. percentil. Da lavere er bedre for arbejdstimer, viser dette tal det maksimale antal timer, du risikerer at skulle arbejde for at klare regningerne under en kriselignende recession.
            
            **Succesrate:** Procentdelen af de 1.000 universer, hvor depotet i det pågældende år kan dække alle udgifter, så du kan trække dig fuldstændig tilbage (0.0 barista-timer).
            """)
            
        mc_view = st.segmented_control(
            "Vælg visning",
            options=["Median (Forventet scenarie)", "P10 (Worst-case scenarie)"],
            default="Median (Forventet scenarie)",
            key=f"mc_view_solo_{ydelse_key_clean}",
            label_visibility="collapsed"
        )
        is_worst_case = (mc_view == "P10 (Worst-case scenarie)")
    else:
        is_worst_case = False

    table_data = []
    
    for year in range(0, 26):
        c_age_j = age_j + year
        current_ret = market_returns[year]
        
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > actual_salgsaar:
            mdr_gaaet = (oml_aar - actual_salgsaar) * 12
            restgaeld_ved_oml = restgaeld_start * ((1 + oprindelig_rente_mnd)**360 - (1 + oprindelig_rente_mnd)**mdr_gaaet) / ((1 + oprindelig_rente_mnd)**360 - 1)
            ny_hovedstol = restgaeld_ved_oml + oml_omk
            mnd_rente_ny = oml_rente / 12
            
            if not oml_afdrag_fri: ny_lån_ydelse = ny_hovedstol * (mnd_rente_ny * (1 + mnd_rente_ny)**360) / ((1 + mnd_rente_ny)**360 - 1)
            else: ny_lån_ydelse = ny_hovedstol * mnd_rente_ny
                
            renter_md = (ny_hovedstol * oml_rente) / 12
            netto_bolig_total = ny_lån_ydelse + ejerudgifter_total + boligskat_md - (renter_md * 0.256)
            diff_bolig = bolig_total_current - netto_bolig_total
            start_fire_j -= diff_bolig; start_inv_md_j += diff_bolig
            bolig_total_current = netto_bolig_total

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate)
            
            if actual_salgsaar > 0 and year <= actual_salgsaar:
                valby_pris_stigning = valby_pris * global_bolig_inflation
                maal_pris_stigning = maal_pris * global_bolig_inflation
                asymmetrisk_gevinst = valby_pris_stigning - maal_pris_stigning
                
                valby_pris += valby_pris_stigning
                maal_pris += maal_pris_stigning
                
                locked_frivaerdi_j += 84000 + asymmetrisk_gevinst
                
                if year == actual_salgsaar:
                    skaleret_udbetaling_j = udbetaling_j * (maal_pris / boligpris)
                    fakt_udb_j = min(skaleret_udbetaling_j, locked_frivaerdi_j)
                    
                    depot_free_j += max(0, locked_frivaerdi_j - fakt_udb_j)
                    
                    ny_ydelse = realkreditydelse_netto * (maal_pris / boligpris)
                    ny_ejerudgifter = ejerudgifter_total * ((1 + global_inflation_rate)**year)
                    ny_boligskat = boligskat_md * ((1 + global_inflation_rate)**year)
                    ny_bolig_total = ny_ydelse + ny_ejerudgifter + ny_boligskat
                    
                    valby_total_nu = bolig_total_current * ((1 + global_inflation_rate)**year)
                    diff_bolig = valby_total_nu - ny_bolig_total
                    
                    start_fire_j -= diff_bolig
                    diff_bolig_base = diff_bolig / ((1 + global_inflation_rate)**year)
                    start_inv_md_j += diff_bolig_base
                    
                    bolig_total_current = ny_bolig_total / ((1 + global_inflation_rate)**year)
                    restgaeld_start = maal_pris - fakt_udb_j

            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            return_frie_j = depot_free_j * current_ret
            tax_j = np.where(return_frie_j <= prog_limit_j, return_frie_j * 0.27, prog_limit_j * 0.27 + (return_frie_j - prog_limit_j) * 0.42)
            
            depot_free_j = np.maximum(0, depot_free_j + (return_frie_j - tax_j))
            depot_ask_j = np.maximum(0, depot_ask_j * (1 + current_ret * 0.83))
            
            depot_free_j += np.where(~j_reached_arr, start_inv_md_j * 12 * ((1 + global_inflation_rate)**year), 0)

            ask_limit_year = ask_base_limit * ((1 + global_inflation_rate)**year)
            space_j = np.maximum(0, ask_limit_year - depot_ask_j)
            move_j = np.minimum(space_j, np.maximum(0, depot_free_j))
            depot_ask_j += move_j
            depot_free_j -= move_j
            
            pension_j_current = np.maximum(0, pension_j_current * (1 + (current_ret * (1 - pal_tax))))
            pension_j_current += np.where(~j_reached_arr, st.session_state["pension_indb_j"] * 12 * ((1 + global_inflation_rate)**year), 0)

        p_j = calculate_drawdown_monthly_income(np.maximum(0, depot_ask_j + depot_free_j), c_age_j, pensionsalder_j, global_return_rate_net_drawdown, global_inflation_rate, use_real_drawdown)
        h_j_array = np.maximum(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        j_reached_arr = j_reached_arr | (h_j_array <= 0)

        if n_sims > 1:
            med_dep_j = np.median(depot_ask_j + depot_free_j)
            p10_dep_j = np.percentile(depot_ask_j + depot_free_j, 10)
            med_p_j = np.median(p_j)
            p10_p_j = np.percentile(p_j, 10)
            med_h_j = np.median(h_j_array)
            p90_h_j = np.percentile(h_j_array, 90)
            succ_j = np.mean(h_j_array <= 0) * 100

            if is_worst_case:
                table_data.append({
                    "År": year, 
                    "Alder": c_age_j, 
                    "Depot (M)": f"{p10_dep_j/1e6:.2f}", 
                    "Passiv Indkomst (kr)": f"{int(p10_p_j):,}".replace(',', '.'), 
                    "Arbejdstid (Barista)": f"{get_emoji_status(p90_h_j).split()[0]} {p90_h_j:.1f}t",
                    "Succesrate": f"{succ_j:.0f}%"
                })
            else:
                table_data.append({
                    "År": year, 
                    "Alder": c_age_j, 
                    "Depot (M)": f"{med_dep_j/1e6:.2f}", 
                    "Passiv Indkomst (kr)": f"{int(med_p_j):,}".replace(',', '.'), 
                    "Arbejdstid (Barista)": get_emoji_status(med_h_j),
                    "Succesrate": f"{succ_j:.0f}%"
                })
        else:
            table_data.append({
                "År": year, 
                "Alder": c_age_j, 
                "Depot (M)": f"{(depot_ask_j[0] + depot_free_j[0])/1e6:.2f}", 
                "Passiv Indkomst (kr)": f"{int(p_j[0]):,}".replace(',', '.'), 
                "Arbejdstid (Barista)": get_emoji_status(h_j_array[0])
            })
            if j_reached_arr[0]: break

    st.table(pd.DataFrame(table_data).set_index("År"))
    
    with st.expander("🔄 Omlægningsscenarie", expanded=False):
        st.toggle("Aktiver omlægningsscenarie", value=False, key=f"aktiver_oml_{ydelse_key_clean}", on_change=clear_preset)
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        col_o1.number_input("År for omlægning efter salg (1-10)", min_value=1, max_value=10, value=5, key=f"oml_aar_{ydelse_key_clean}", on_change=clear_preset)
        col_o2.number_input("Ny rente + bidrag (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1, key=f"oml_rente_{ydelse_key_clean}", on_change=clear_preset)
        col_o3.toggle("Afdragsfrihed aktiveret", value=False, key=f"oml_afdrag_fri_{ydelse_key_clean}", on_change=clear_preset)
        col_o4.number_input("Omkostninger (kr)", value=50000, step=5000, key=f"oml_omk_{ydelse_key_clean}", on_change=clear_preset)


# --- VISNING 1: OPSÆTNING ---
if view_selection == "⚙️ Basisdata & Opsætning":
    st.subheader("Konfiguration af personlig økonomi")
    
    # --- FÆLLES UDGIFTER MODUL ---
    st.markdown("### 🛒 Fælles Udgifter (Mad)")
    col_mad1, col_mad2 = st.columns(2)
    with col_mad1:
        st.session_state["mad_total_val"] = st.number_input("Samlet månedligt madbudget (kr.)", min_value=0, value=st.session_state["mad_total_val"], step=500, key="total_mad_input", on_change=clear_preset)
    with col_mad2:
        st.session_state["mad_j_val"] = st.slider("Johans andel af madbudgettet", min_value=0, max_value=int(st.session_state["mad_total_val"]), value=min(st.session_state["mad_j_val"], int(st.session_state["mad_total_val"])), step=100, key="mad_slider_j", on_change=clear_preset)
    
    # Opdater automatisk budgetterne ud fra gemte variabler
    st.session_state["budget_j"]["Mad"] = st.session_state["mad_j_val"]
    st.session_state["budget_m"]["Mad"] = int(st.session_state["mad_total_val"]) - st.session_state["mad_j_val"]
    
    st.write("")
    st.divider()
    
    col_setup_j, col_setup_m = st.columns(2)
    
    with col_setup_j:
        st.markdown("### 👤 JOHAN DATA")
        st.session_state["inkomst_j"] = st.number_input("Månedsløn (Netto kr.)", value=st.session_state["inkomst_j"], step=500, key="inp_j", on_change=clear_preset)
        st.session_state["pension_j"] = st.number_input("Pensionsopsparing (kr.)", min_value=0, value=st.session_state["pension_j"], step=10000, key="input_pen_j", on_change=clear_preset)
        st.session_state["pension_indb_j"] = st.number_input("Arbejdsgiverpension (mdl. kr.)", min_value=0, value=st.session_state["pension_indb_j"], step=500, key="indb_pen_j", on_change=clear_preset)
        st.session_state["cash_j_base"] = st.number_input("Kontanter / Friværdi (kr.)", value=st.session_state["cash_j_base"], step=10000, key="csh_j", on_change=clear_preset)
        st.session_state["basis_ask_j"] = st.number_input("Aktiesparekonto (kr.)", value=st.session_state["basis_ask_j"], key="ask_j", on_change=clear_preset)
        st.session_state["basis_frie_j"] = st.number_input("Frie midler / Aktier (kr.)", value=st.session_state["basis_frie_j"], key="fr_j", on_change=clear_preset)
        
        st.session_state["use_loensikring_j"] = st.toggle("Inddrag Lønsikring (1.836 kr.)", value=st.session_state.get("use_loensikring_j", False), key="toggle_loen_j", on_change=clear_preset)
        st.session_state["budget_j"]["Loensikring"] = 1836 if st.session_state["use_loensikring_j"] else 0
        
        df_j = st.data_editor(pd.DataFrame(list(st.session_state["budget_j"].items()), columns=["Kategori", "Beløb"]), hide_index=True, use_container_width=True, key="ed_j", on_change=clear_preset)
        st.session_state["budget_j"] = dict(df_j.values)
        st.write("")
        
    with col_setup_m:
        st.markdown("### 👤 MARKUS DATA")
        st.session_state["inkomst_m"] = st.number_input("Månedsløn (Netto kr.)", value=st.session_state["inkomst_m"], step=500, key="inp_m", on_change=clear_preset)
        st.session_state["pension_m"] = st.number_input("Pensionsopsparing (kr.)", min_value=0, value=st.session_state["pension_m"], step=10000, key="input_pen_m", on_change=clear_preset)
        st.session_state["pension_indb_m"] = st.number_input("Arbejdsgiverpension (mdl. kr.)", min_value=0, value=st.session_state["pension_indb_m"], step=500, key="indb_pen_m", on_change=clear_preset)
        st.session_state["cash_m_base"] = st.number_input("Kontanter / Friværdi (kr.)", value=st.session_state["cash_m_base"], step=10000, key="csh_m", on_change=clear_preset)
        st.session_state["basis_ask_m"] = st.number_input("Aktiesparekonto (kr.)", value=st.session_state["basis_ask_m"], key="ask_m", on_change=clear_preset)
        st.session_state["basis_frie_m"] = st.number_input("Frie midler / Aktier (kr.)", value=st.session_state["basis_frie_m"], key="fr_m", on_change=clear_preset)
        
        st.session_state["use_loensikring_m"] = st.toggle("Inddrag Lønsikring (720 kr.)", value=st.session_state.get("use_loensikring_m", False), key="toggle_loen_m", on_change=clear_preset)
        st.session_state["budget_m"]["Loensikring"] = 720 if st.session_state["use_loensikring_m"] else 0
        
        df_m = st.data_editor(pd.DataFrame(list(st.session_state["budget_m"].items()), columns=["Kategori", "Beløb"]), hide_index=True, use_container_width=True, key="ed_m", on_change=clear_preset)
        st.session_state["budget_m"] = dict(df_m.values)
        st.write("")
        st.session_state["use_bsu_m"] = st.toggle("Inddrag Norsk BSU", value=st.session_state.get("use_bsu_m", False), key="toggle_bsu_m", on_change=clear_preset)

# --- VISNING 2: SCENARIER ---
else:
    is_solo_mode = False
    if st.session_state.get("secret_id", "").strip().lower() == "solo": is_solo_mode = True
    try:
        if "mode" in st.query_params and st.query_params["mode"] == "solo": is_solo_mode = True
    except: pass

    tab_names = ["3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby"]
    if is_solo_mode: tab_names.extend(["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"])
    
    tabs = st.tabs(tab_names)

    with tabs[0]: simulate_joint_fire_plan("3.5M", 3500000, 966000, 434000, 8516, "yd35", 4564, True, 1600)
    with tabs[1]: simulate_joint_fire_plan("4.0M", 4000000, 1846222, 1153888, 4075, "yd40", 4564, True, 1850)
    with tabs[2]: simulate_joint_fire_plan("4.5M", 4500000, 2250000, 1125000, 4576, "yd45", 4564, True, 2050)
    with tabs[3]: simulate_joint_fire_plan("5.0M", 5000000, 2408888, 983888, 6519, "yd50", 4564, True, 2300)
    with tabs[4]: simulate_joint_fire_plan("5.5M", 5500000, 1515000, 685000, 13659, "yd55", 4564, True, 2550)
    with tabs[5]: simulate_joint_fire_plan("Valby", 6700000, 0, 0, 15230, "ydvb", 4564, False, 0)

    if is_solo_mode:
        with tabs[6]: simulate_solo_fire_plan("3.0M", 3000000, 1200000, 7308, "yds30", 3500, 1400)
        with tabs[7]: simulate_solo_fire_plan("3.5M", 3500000, 1400000, 8516, "yds35", 4000, 1600)
        with tabs[8]: simulate_solo_fire_plan("4.0M", 4000000, 1600000, 9724, "yds40", 4500, 1850)
