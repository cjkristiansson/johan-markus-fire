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
if "basis_ask_j" not in st.session_state: st.session_state["basis_ask_j"] = 185300
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 129573
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
if "mc_active" not in st.session_state: st.session_state["mc_active"] = True

# Valby Pris Input
if "valby_pris_input" not in st.session_state: st.session_state["valby_pris_input"] = 6600000

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
    * **Udskudt Salg:** Hvis salget udskydes, låses friværdien. Modellen fremskriver asymmetrisk boliginflation og faste afdrag frem til Salgsåret.
    * **Monte Carlo Simulering:** Kører 1.000 parallelle universer vektoriseret i NumPy baseret på historisk volatilitet for at stressteste Barista-tilværelsen.
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

def clear_preset():
    st.session_state["active_preset"] = "Custom"

def toggle_mc():
    st.session_state["mc_active"] = not st.session_state.get("mc_active", False)

# Knapper
st.sidebar.button("Standard", type="primary" if st.session_state["active_preset"] == "Standard" else "secondary", use_container_width=True, on_click=set_preset, args=("Standard",))
st.sidebar.button("Realistisk", type="primary" if st.session_state["active_preset"] == "Realistisk" else "secondary", use_container_width=True, on_click=set_preset, args=("Realistisk",))
st.sidebar.button("Konservativ", type="primary" if st.session_state["active_preset"] == "Konservativ" else "secondary", use_container_width=True, on_click=set_preset, args=("Konservativ",), disabled=st.session_state.get("mc_active", False), help="Deaktiveret under Monte Carlo for at forhindre bias i P10 scenariet.")

global_return_rate_gross = st.sidebar.slider("Bruttoafkast under opsparing (%)", min_value=3.0, max_value=10.0, step=0.5, on_change=clear_preset, key="slider_return") / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast i passiv fase (%)", min_value=2.0, max_value=8.0, step=0.1, on_change=clear_preset, key="slider_drawdown") / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", min_value=0.0, max_value=5.0, step=0.5, on_change=clear_preset, key="slider_inflation") / 100

st.sidebar.toggle("Købekraftsjusteret udtræk i FIRE-fasen", key="use_real_drawdown", help="Tvinger modellen til at reservere en del af aktieafkastet til at beskytte hovedstolen mod inflation. Resulterer i en lavere start-udbetaling, der til gengæld stiger år for år for at fastholde købekraften.", on_change=clear_preset)

st.sidebar.divider()
st.sidebar.markdown("### Monte Carlo Simulering", help="Stresstester din FIRE-plan ved at køre 1.000 parallelle markedsforløb. Det kvantificerer risikoen for at ramme et krak tidligt i forløbet (Sequence of Returns Risk).")
mc_volatility = st.sidebar.slider("Markedsvolatilitet (%)", min_value=5.0, max_value=25.0, value=15.0, step=1.0, on_change=clear_preset) / 100
mc_btn_label = "Slå Monte Carlo FRA" if st.session_state.get("mc_active", False) else "Beregn Monte Carlo"
st.sidebar.button(mc_btn_label, type="primary", use_container_width=True, on_click=toggle_mc)

st.sidebar.divider()
st.sidebar.markdown("### Salg af Valby-lejlighed")
global_salgsaar = st.sidebar.slider("Salgsår (0 = Sælg nu)", min_value=0, max_value=10, value=0, step=1, on_change=clear_preset)
global_bolig_inflation = st.sidebar.slider("Boligmarkedsvækst (Asymmetrisk gevinst %)", min_value=-10.0, max_value=10.0, value=3.0, step=0.5, on_change=clear_preset) / 100

st.sidebar.divider()
st.sidebar.markdown("### Skattepolitik")
st.sidebar.toggle("Hæv ASK-loft til 500.000 kr.", key="use_ask_500k", on_change=clear_preset)

st.sidebar.divider()
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5, on_change=clear_preset)
pensionsalder_j = st.sidebar.number_input("Johans pensionsalder", min_value=55, max_value=75, value=67, step=1, on_change=clear_preset)
pensionsalder_m = st.sidebar.number_input("Markus' pensionsalder", min_value=55, max_value=75, value=65, step=1, on_change=clear_preset)

st.sidebar.divider()
st.sidebar.text_input("Gendan Scenarie-ID", help="Indtast ID for at indlæse specifik konfiguration (f.eks. 'solo').", key="secret_id")

# --- SIKRE HJÆLPEFUNKTIONER ---
def format_dkk(amount):
    try:
        if pd.isna(amount) or np.isnan(amount) or np.isinf(amount):
            return "0"
        return f"{int(amount):,}".replace(',', '.')
    except:
        return "0"

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
    try:
        if pd.isna(barista_hours) or np.isnan(barista_hours) or np.isinf(barista_hours):
            return "🏁 0.0t"
        if barista_hours <= 0: return "🏁 0.0t"
        elif 0 < barista_hours <= 15: return f"🟡 {barista_hours:.1f}t"
        elif 15 < barista_hours <= 25: return f"🟠 {barista_hours:.1f}t"
        else: return f"🔴 {barista_hours:.1f}t"
    except:
        return "🏁 0.0t"

# --- DYNAMISKE SIMULERINGSFUNKTIONER ---
def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, ydelse_default, ydelse_key, ejerudgifter_standard, bolig_solgt):
    pal_tax, weeks_per_month, age_j, age_m = 0.153, 4.33, 41, 32
    ydelse_key_clean = ydelse_key.replace("solo_", "")
    
    nuvaerende_afdragsfri = st.session_state.get(f"nuvaerende_afdragsfri_{ydelse_key_clean}", False)
    ejerudgifter_input = st.session_state.get(f"ejer_{ydelse_key_clean}", int(ejerudgifter_standard))
    mangler_skat = st.session_state.get(f"mangler_skat_{ydelse_key_clean}", False)
    
    skat_tillaeg = int((boligpris * 0.0055) / 12) if mangler_skat else 0
    effektiv_ejerudgift = ejerudgifter_input + skat_tillaeg

    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key_clean}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key_clean}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{ydelse_key_clean}", 4.0) / 100
    oml_bidrag = st.session_state.get(f"oml_bidrag_{ydelse_key_clean}", 0.45) / 100
    oml_total_rente = oml_rente + oml_bidrag
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{ydelse_key_clean}", True)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key_clean}", 50000)
    use_equity = st.session_state.get(f"use_equity_{ydelse_key_clean}", False)
    equity_amt = st.session_state.get(f"equity_amount_{ydelse_key_clean}", 1000000) if use_equity else 0

    use_real_drawdown = st.session_state.get("use_real_drawdown", False)
    use_ask_500k = st.session_state.get("use_ask_500k", False)
    ask_base_limit = 500000 if use_ask_500k else 174000

    # MC Logik
    is_mc = st.session_state.get("mc_active", False)
    n_sims = 1000 if is_mc else 1
    vol = mc_volatility if is_mc else 0.0
    market_returns = np.random.normal(loc=global_return_rate_gross, scale=vol, size=(26, n_sims))

    is_valby = "Valby" in scenario_name
    actual_salgsaar = 0 if is_valby else global_salgsaar
    
    # Dynamisk Valby Pris
    valby_pris = st.session_state.get("valby_pris_input", 6600000)
    maal_pris = boligpris

    use_bsu = st.session_state.get("use_bsu_m", False)
    bsu_amount = 292060
    
    cash_j = st.session_state["cash_j_base"] if bolig_solgt else 0
    cash_m = st.session_state["cash_m_base"] if bolig_solgt else 0
    
    valby_fast_restgaeld = 3059064
    valby_afdrag_md = 0 if nuvaerende_afdragsfri else 6930
    
    with st.expander("🏠 Vis økonomiske detaljer & lån", expanded=False):
        if actual_salgsaar > 0:
            st.info(f"⏳ **Salg udskudt til År {actual_salgsaar}.** Jeres nuværende Valby-friværdi er låst i mursten indtil da.")
            
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        target_total_udb = udbetaling_j + udbetaling_m
        ui_cash_pct = (target_total_udb / boligpris * 100) if boligpris > 0 else 0
        ui_loan_pct = 100 - ui_cash_pct

        with col_inp:
            udb_str = f"{target_total_udb/1e6:g}".replace('.', ',')
            st.markdown(f"<p style='margin-bottom: 15px; margin-top: 0; line-height: 1.3;'>Mål: {int(ui_cash_pct)}% udb. ({udb_str}M) | {int(ui_loan_pct)}% lån</p>", unsafe_allow_html=True)
            
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key, on_change=clear_preset)

            effektiv_realkreditydelse = realkreditydelse_netto
            if is_valby and nuvaerende_afdragsfri:
                effektiv_realkreditydelse = max(0, realkreditydelse_netto - 6930)
                st.markdown("<p style='font-size: 0.8em; color: gray; margin-top: -10px;'>* Reduceret pga. afdragsfrihed</p>", unsafe_allow_html=True)

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
            st.error("⚠️ ADVARSEL: Udbetalingen overstiger jeres likviditet.")

        base_frie_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        base_frie_m = st.session_state["basis_frie_m"] + (cash_m - faktisk_udbetaling_m)
        
        bolig_faelles_current = (effektiv_realkreditydelse + effektiv_ejerudgift) / 2
        restgaeld_start = valby_fast_restgaeld if is_valby else (boligpris - (faktisk_udbetaling_j + faktisk_udbetaling_m))
        
        locked_frivaerdi_j = 0.0
        locked_frivaerdi_m = 0.0
    else:
        bsu_passive = 983 if use_bsu else 983
        faktisk_udbetaling_j = 0
        faktisk_udbetaling_m = 0
        
        base_frie_j = st.session_state["basis_frie_j"]
        base_frie_m = st.session_state["basis_frie_m"]
        
        valby_ydelse = 15230 - 6930 if nuvaerende_afdragsfri else 15230
        bolig_faelles_current = (valby_ydelse + 3374) / 2
        restgaeld_start = valby_fast_restgaeld
        
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

    space_j_init = np.maximum(0, ask_base_limit - depot_ask_j)
    move_j = np.minimum(space_j_init, np.maximum(0, depot_free_j))
    depot_ask_j += move_j
    depot_free_j -= move_j

    space_m_init = np.maximum(0, ask_base_limit - depot_ask_m)
    move_m = np.minimum(space_m_init, np.maximum(0, depot_free_m))
    depot_ask_m += move_m
    depot_free_m -= move_m

    with col_inp:
        budget_j_total = sum(st.session_state["budget_j"].values())
        budget_m_total = sum(st.session_state["budget_m"].values())

        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_faelles_current)
        start_inv_md_m = st.session_state["inkomst_m"] - (budget_m_total + bolig_faelles_current) + bsu_passive
        
        start_fire_j = sum(v for k, v in st.session_state["budget_j"].items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_faelles_current
        start_fire_m = sum(v for k, v in st.session_state["budget_m"].items() if k not in ["A_kasse_Fagforening", "Loensikring", "Studielaan"]) + bolig_faelles_current

        udb_j_str = format_dkk(udbetaling_j)
        ydelse_j_str = format_dkk(effektiv_realkreditydelse / 2)
        ejer_j_str = format_dkk(effektiv_ejerudgift / 2)
        depot_j_str = format_dkk(depot_free_j[0] + depot_ask_j[0])
        inv_md_j_str = format_dkk(start_inv_md_j)
        fire_j_str = format_dkk(start_fire_j)

        udb_m_str = format_dkk(udbetaling_m)
        ydelse_m_str = format_dkk(effektiv_realkreditydelse / 2)
        ejer_m_str = format_dkk(effektiv_ejerudgift / 2)
        depot_m_str = format_dkk(depot_free_m[0] + depot_ask_m[0])
        inv_md_m_str = format_dkk(start_inv_md_m)
        fire_m_str = format_dkk(start_fire_m)

    with col_j:
        st.subheader("JOHAN")
        st.markdown(f"""
        **Mål-Udbetaling:** {udb_j_str} kr.  
        **Realkredit (egen andel):** {ydelse_j_str} kr./md.  
        **Ejerudgifter (egen andel):** {ejer_j_str} kr./md.  
        **Startdepot (År 0):** {depot_j_str} kr.  
        **Mdl. opsparing (År 0):** {inv_md_j_str} kr.  
        **Mdl. Udgifter (År 0):** {fire_j_str} kr./md.
        """)
    
    with col_m:
        st.subheader("MARKUS")
        st.markdown(f"""
        **Mål-Udbetaling:** {udb_m_str} kr.  
        **Realkredit (egen andel):** {ydelse_m_str} kr./md.  
        **Ejerudgifter (egen andel):** {ejer_m_str} kr./md.  
        **Startdepot (År 0):** {depot_m_str} kr.  
        **Mdl. opsparing (År 0):** {inv_md_m_str} kr.  
        **Mdl. Udgifter (År 0):** {fire_m_str} kr./md.
        """)

    # --- UI: PLACERING OVER TABEL (Ejerudgift & Toggle) ---
    st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
    col_spacer, col_tog, col_ejer = st.columns([0.5, 0.3, 0.2], vertical_alignment="bottom")
    with col_tog:
        st.toggle("Ejerudgift ekskl. 2024-skat", key=f"mangler_skat_{ydelse_key_clean}", on_change=clear_preset)
        if st.session_state.get(f"mangler_skat_{ydelse_key_clean}", False) and boligpris > 0:
            st.markdown(f"<div style='font-size: 0.8em; color: gray; margin-top: -10px; margin-bottom: 5px;'>ℹ️ +{skat_tillaeg} kr./md. tilføjet</div>", unsafe_allow_html=True)
    with col_ejer:
        st.number_input("Ejerudgift (kr./md.)", value=int(ejerudgifter_standard), step=100, key=f"ejer_{ydelse_key_clean}", on_change=clear_preset)

    if is_mc:
        mc_view = st.radio("Vælg Monte Carlo Visning", options=["P10 (Worst-case scenarie)", "Median (Forventet scenarie)"], index=1, horizontal=True, key=f"mc_view_joint_{ydelse_key_clean}", label_visibility="collapsed")
        is_worst_case = (mc_view == "P10 (Worst-case scenarie)")
    else:
        is_worst_case = False

    table_data = []
    
    for year in range(0, 26):
        c_age_j, c_age_m = age_j + year, age_m + year
        current_ret = market_returns[year]
        
        # Omlægningsscenarie Logik
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > actual_salgsaar:
            if is_valby:
                if nuvaerende_afdragsfri:
                    if oml_aar <= 10:
                        afdraget_beloeb = 0
                    else:
                        mdr_tilbage_ved_10 = (27 - 10) * 12
                        ny_valby_ydelse = valby_fast_restgaeld * (0.002 * (1.002)**mdr_tilbage_ved_10) / ((1.002)**mdr_tilbage_ved_10 - 1)
                        nyt_afdrag_md = ny_valby_ydelse - 8300
                        afdraget_beloeb = nyt_afdrag_md * 12 * (oml_aar - 10)
                else:
                    afdraget_beloeb = valby_afdrag_md * 12 * oml_aar
                restgaeld_ved_oml = max(0, restgaeld_start - afdraget_beloeb)
            else:
                mdr_gaaet = (oml_aar - actual_salgsaar) * 12
                restgaeld_ved_oml = restgaeld_start * ((1 + oprindelig_rente_mnd)**360 - (1 + oprindelig_rente_mnd)**mdr_gaaet) / ((1 + oprindelig_rente_mnd)**360 - 1)
            
            ny_hovedstol = restgaeld_ved_oml + oml_omk + equity_amt
            mnd_rente_ny = oml_total_rente / 12
            
            if mnd_rente_ny > 0:
                factor = (1 + mnd_rente_ny)**360
                if not oml_afdrag_fri: ny_lån_ydelse = ny_hovedstol * (mnd_rente_ny * factor) / (factor - 1)
                else: ny_lån_ydelse = ny_hovedstol * mnd_rente_ny
            else:
                ny_lån_ydelse = ny_hovedstol / 360 if not oml_afdrag_fri else 0.0
                
            renter_md = (ny_hovedstol * oml_total_rente) / 12
            current_ejerudgifter = 3374 * ((1 + global_inflation_rate)**year) if (is_valby and year <= actual_salgsaar) else effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
            
            netto_bolig_faelles = (ny_lån_ydelse + current_ejerudgifter - (renter_md * 0.256)) / 2
            diff_faelles = bolig_faelles_current - netto_bolig_faelles
            start_fire_j -= diff_faelles; start_fire_m -= diff_faelles
            start_inv_md_j += diff_faelles; start_inv_md_m += diff_faelles
            bolig_faelles_current = netto_bolig_faelles
            
            depot_free_j += (equity_amt / 2); depot_free_m += (equity_amt / 2)

        # Udløb af nuværende afdragsfrihed i Valby (År 10 chok)
        if is_valby and nuvaerende_afdragsfri and year == 10:
            if not (aktiver_oml and oml_aar <= 10) and (actual_salgsaar == 0 or actual_salgsaar > 10):
                mdr_tilbage = (27 - 10) * 12
                rente_mnd = 0.024 / 12
                ny_valby_ydelse = valby_fast_restgaeld * (rente_mnd * (1 + rente_mnd)**mdr_tilbage) / ((1 + rente_mnd)**mdr_tilbage - 1)
                ekstra_nominel_ydelse = ny_valby_ydelse - 8300
                valby_afdrag_md = ekstra_nominel_ydelse
                
                start_fire_j += (ekstra_nominel_ydelse / 2); start_fire_m += (ekstra_nominel_ydelse / 2)
                start_inv_md_j -= (ekstra_nominel_ydelse / 2); start_inv_md_m -= (ekstra_nominel_ydelse / 2)
                bolig_faelles_current += (ekstra_nominel_ydelse / 2)

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate); start_fire_m *= (1 + global_inflation_rate)
            
            if actual_salgsaar > 0 and year <= actual_salgsaar:
                valby_pris_stigning = valby_pris * global_bolig_inflation
                maal_pris_stigning = maal_pris * global_bolig_inflation
                asymmetrisk_gevinst = valby_pris_stigning - maal_pris_stigning
                
                valby_pris += valby_pris_stigning
                maal_pris += maal_pris_stigning
                
                locked_frivaerdi_j += (valby_afdrag_md * 12 / 2) + (asymmetrisk_gevinst / 2)
                locked_frivaerdi_m += (valby_afdrag_md * 12 / 2) + (asymmetrisk_gevinst / 2)
                
                if year == actual_salgsaar:
                    skaleret_udbetaling_j = udbetaling_j * (maal_pris / boligpris)
                    skaleret_udbetaling_m = udbetaling_m * (maal_pris / boligpris)
                    
                    if use_bsu:
                        locked_frivaerdi_m += bsu_amount
                        skaleret_udbetaling_j -= (bsu_amount / 2); skaleret_udbetaling_m += (bsu_amount / 2)
                        bsu_passive = 0; start_inv_md_m -= 983
                        
                    mangler_m = max(0, skaleret_udbetaling_m - locked_frivaerdi_m)
                    fakt_udb_m = skaleret_udbetaling_m - mangler_m
                    udb_j_tot = skaleret_udbetaling_j + mangler_m
                    fakt_udb_j = udb_j_tot - max(0, udb_j_tot - locked_frivaerdi_j)
                    
                    depot_free_j += max(0, locked_frivaerdi_j - fakt_udb_j)
                    depot_free_m += max(0, locked_frivaerdi_m - fakt_udb_m)
                    
                    ny_ydelse = realkreditydelse_netto * (maal_pris / boligpris)
                    ny_ejerudgifter = effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
                    ny_bolig_faelles = (ny_ydelse + ny_ejerudgifter) / 2
                    
                    diff_faelles = (bolig_faelles_current * ((1 + global_inflation_rate)**year)) - ny_bolig_faelles
                    start_fire_j -= diff_faelles; start_fire_m -= diff_faelles
                    start_inv_md_j += (diff_faelles / ((1 + global_inflation_rate)**year)); start_inv_md_m += (diff_faelles / ((1 + global_inflation_rate)**year))
                    
                    bolig_faelles_current = ny_bolig_faelles / ((1 + global_inflation_rate)**year)
                    restgaeld_start = maal_pris - (fakt_udb_j + fakt_udb_m)

            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            prog_limit_m = 79400 * ((1 + global_inflation_rate)**year)
            
            return_frie_j = depot_free_j * current_ret; return_frie_m = depot_free_m * current_ret
            tax_j = np.where(return_frie_j <= prog_limit_j, return_frie_j * 0.27, prog_limit_j * 0.27 + (return_frie_j - prog_limit_j) * 0.42)
            tax_m = np.where(return_frie_m <= prog_limit_m, return_frie_m * 0.27, prog_limit_m * 0.27 + (return_frie_m - prog_limit_m) * 0.42)
            
            depot_free_j = np.maximum(0, depot_free_j + (return_frie_j - tax_j))
            depot_free_m = np.maximum(0, depot_free_m + (return_frie_m - tax_m))
            depot_ask_j = np.maximum(0, depot_ask_j * (1 + current_ret * 0.83))
            depot_ask_m = np.maximum(0, depot_ask_m * (1 + current_ret * 0.83))
            
            depot_free_j += np.where(~j_reached_arr, start_inv_md_j * 12 * ((1 + global_inflation_rate)**year), 0)
            depot_free_m += np.where(~m_reached_arr, start_inv_md_m * 12 * ((1 + global_inflation_rate)**year), 0)

            ask_limit_year = ask_base_limit * ((1 + global_inflation_rate)**year)
            space_j = np.maximum(0, ask_limit_year - depot_ask_j); move_j = np.minimum(space_j, np.maximum(0, depot_free_j))
            depot_ask_j += move_j; depot_free_j -= move_j

            space_m = np.maximum(0, ask_limit_year - depot_ask_m); move_m = np.minimum(space_m, np.maximum(0, depot_free_m))
            depot_ask_m += move_m; depot_free_m -= move_m

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
            med_dep_j = np.median(depot_ask_j + depot_free_j); p10_dep_j = np.percentile(depot_ask_j + depot_free_j, 10)
            med_p_j = np.median(p_j); p10_p_j = np.percentile(p_j, 10)
            med_h_j = np.median(h_j_array); p90_h_j = np.percentile(h_j_array, 90)
            succ_j = np.mean(h_j_array <= 0) * 100

            med_dep_m = np.median(depot_ask_m + depot_free_m); p10_dep_m = np.percentile(depot_ask_m + depot_free_m, 10)
            med_p_m = np.median(p_m_total); p10_p_m = np.percentile(p_m_total, 10)
            med_h_m = np.median(h_m_array); p90_h_m = np.percentile(h_m_array, 90)
            succ_m = np.mean(h_m_array <= 0) * 100

            if is_worst_case:
                table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{p10_dep_j/1e6:.2f}", "J.Passiv (kr)": format_dkk(p10_p_j), "J.Arbtid": f"{get_emoji_status(p90_h_j).split()[0]} {p90_h_j:.1f}t", "J.Succes": f"{succ_j:.0f}%", "M.alder": c_age_m, "M.depot (M)": f"{p10_dep_m/1e6:.2f}", "M.Passiv (kr)": format_dkk(p10_p_m), "M.Arbtid": f"{get_emoji_status(p90_h_m).split()[0]} {p90_h_m:.1f}t", "M.Succes": f"{succ_m:.0f}%"})
            else:
                table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{med_dep_j/1e6:.2f}", "J.Passiv (kr)": format_dkk(med_p_j), "J.Arbtid": get_emoji_status(med_h_j), "J.Succes": f"{succ_j:.0f}%", "M.alder": c_age_m, "M.depot (M)": f"{med_dep_m/1e6:.2f}", "M.Passiv (kr)": format_dkk(med_p_m), "M.Arbtid": get_emoji_status(med_h_m), "M.Succes": f"{succ_m:.0f}%"})
        else:
            table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{(depot_ask_j[0] + depot_free_j[0])/1e6:.2f}", "J.Passiv (kr)": format_dkk(p_j[0]), "J.Arbtid": get_emoji_status(h_j_array[0]), "M.alder": c_age_m, "M.depot (M)": f"{(depot_ask_m[0] + depot_free_m[0])/1e6:.2f}", "M.Passiv (kr)": format_dkk(p_m_total[0]), "M.Arbtid": get_emoji_status(h_m_array[0])})
            if j_reached_arr[0] and m_reached_arr[0]: break

    st.table(pd.DataFrame(table_data).set_index("År"))
    st.write("")
    
    if is_valby or actual_salgsaar > 0:
        st.markdown("### 🔒 Styring af nuværende Valby lån")
        st.toggle("Aktiver afdragsfrihed på nuværende lån (Valby)", key=f"nuvaerende_afdragsfri_{ydelse_key_clean}", on_change=clear_preset, help="Fjerner afdraget på 6.930 kr. fra budgettet, men udløser et komprimeret afdragschok i år 11.")

    with st.expander("🔄 Scenarie for Omlægning (Nyt lån)", expanded=False):
        st.toggle("Aktiver omlægningsscenarie", value=False, key=f"aktiver_oml_{ydelse_key_clean}", on_change=clear_preset)
        col_o1, col_o2, col_o3 = st.columns(3)
        col_o1.number_input("År for omlægning (0-10)", min_value=0, max_value=10, value=5, key=f"oml_aar_{ydelse_key_clean}", on_change=clear_preset)
        col_o2.number_input("Ny rente (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1, key=f"oml_rente_{ydelse_key_clean}", on_change=clear_preset)
        col_o3.number_input("Nyt bidrag (%)", min_value=0.0, max_value=5.0, value=0.45, step=0.05, key=f"oml_bidrag_{ydelse_key_clean}", on_change=clear_preset)
        col_o4, col_o5 = st.columns(2)
        col_o4.toggle("Afdragsfrihed aktiveret på nyt lån", value=True, key=f"oml_afdrag_fri_{ydelse_key_clean}", on_change=clear_preset)
        col_o5.number_input("Omkostninger (kr)", value=50000, step=5000, key=f"oml_omk_{ydelse_key_clean}", on_change=clear_preset)
        
        st.markdown("##### Friværdinedsparing")
        st.toggle("Hæv friværdi til investering", value=False, key=f"use_equity_{ydelse_key_clean}", on_change=clear_preset)
        if st.session_state.get(f"use_equity_{ydelse_key_clean}", False):
            st.number_input("Beløb til aktiedepot (kr.)", min_value=0, value=1000000, step=100000, key=f"equity_amount_{ydelse_key_clean}", on_change=clear_preset)

def simulate_solo_fire_plan(scenario_name, boligpris, udbetaling_j, ydelse_default, ydelse_key, ejerudgifter_standard):
    pal_tax, weeks_per_month, age_j = 0.153, 4.33, 41
    s_key = f"solo_{ydelse_key}"
    ydelse_key_clean = s_key.replace("solo_", "")
    
    nuvaerende_afdragsfri = st.session_state.get(f"nuvaerende_afdragsfri_{ydelse_key_clean}", False)
    ejerudgifter_input = st.session_state.get(f"ejer_{ydelse_key_clean}", int(ejerudgifter_standard))
    mangler_skat = st.session_state.get(f"mangler_skat_{ydelse_key_clean}", False)
    
    skat_tillaeg = int((boligpris * 0.0055) / 12) if mangler_skat else 0
    effektiv_ejerudgift = ejerudgifter_input + skat_tillaeg

    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key_clean}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key_clean}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{ydelse_key_clean}", 4.0) / 100
    oml_bidrag = st.session_state.get(f"oml_bidrag_{ydelse_key_clean}", 0.45) / 100
    oml_total_rente = oml_rente + oml_bidrag
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{ydelse_key_clean}", True)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key_clean}", 50000)
    use_equity = st.session_state.get(f"use_equity_{ydelse_key_clean}", False)
    equity_amt = st.session_state.get(f"equity_amount_{ydelse_key_clean}", 1000000) if use_equity else 0

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
    
    # Dynamisk Valby Pris
    valby_pris = st.session_state.get("valby_pris_input", 6600000)
    maal_pris = boligpris

    valby_fast_restgaeld = 3059064
    valby_afdrag_md = 0 if nuvaerende_afdragsfri else 6930

    with st.expander("⚙️ Vis økonomiske detaljer & lån", expanded=False):
        if actual_salgsaar > 0:
            st.info(f"⏳ **Salg udskudt til År {actual_salgsaar}.** Jeres nuværende Valby-friværdi er låst i mursten indtil da.")
            
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        with col_inp:
            udb_str = f"{faktisk_udbetaling_j/1e6:g}".replace('.', ',')
            st.markdown(f"<p style='margin-bottom: 15px; margin-top: 0; line-height: 1.3;'>Mål: {int(cash_pct)}% udb. ({udb_str}M) | {int(loan_pct)}% lån</p>", unsafe_allow_html=True)
                
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key, on_change=clear_preset)

            effektiv_realkreditydelse = realkreditydelse_netto
            if is_valby and nuvaerende_afdragsfri:
                effektiv_realkreditydelse = max(0, realkreditydelse_netto - 6930)
                st.markdown("<p style='font-size: 0.8em; color: gray; margin-top: -10px;'>* Reduceret pga. afdragsfrihed</p>", unsafe_allow_html=True)

    if actual_salgsaar == 0:
        base_frie_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        bolig_total_current = effektiv_realkreditydelse + effektiv_ejerudgift
        restgaeld_start = valby_fast_restgaeld if is_valby else (boligpris - faktisk_udbetaling_j)
        locked_frivaerdi_j = 0.0
    else:
        faktisk_udbetaling_j = 0
        base_frie_j = st.session_state["basis_frie_j"]
        valby_ydelse = 15230 - 6930 if nuvaerende_afdragsfri else 15230
        bolig_total_current = valby_ydelse + 3374
        restgaeld_start = valby_fast_restgaeld
        locked_frivaerdi_j = float(cash_j)

    depot_free_j = np.full(n_sims, base_frie_j, dtype=float)
    depot_ask_j = np.full(n_sims, st.session_state["basis_ask_j"], dtype=float)
    pension_j_current = np.full(n_sims, st.session_state["pension_j"], dtype=float)
    j_reached_arr = np.zeros(n_sims, dtype=bool)

    space_j_init = np.maximum(0, ask_base_limit - depot_ask_j)
    move_j = np.minimum(space_j_init, np.maximum(0, depot_free_j))
    depot_ask_j += move_j; depot_free_j -= move_j

    with col_inp:
        solo_budget_j = st.session_state["budget_j"].copy()
        solo_budget_j["Mad"] = 3000
        budget_j_total = sum(solo_budget_j.values())
        
        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_total_current)
        start_fire_j = sum(v for k, v in solo_budget_j.items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_total_current

        udb_j_str = format_dkk(faktisk_udbetaling_j)
        ydelse_j_str = format_dkk(effektiv_realkreditydelse)
        ejer_j_str = format_dkk(effektiv_ejerudgift)
        depot_j_str = format_dkk(depot_free_j[0] + depot_ask_j[0])
        inv_md_j_str = format_dkk(start_inv_md_j)
        fire_j_str = format_dkk(start_fire_j)
        boligpris_str = format_dkk(boligpris)

    with col_j:
        st.subheader("JOHAN (SOLO)")
        st.markdown(f"""
        **Boligpris:** {boligpris_str} kr.  
        **Mål-Udbetaling:** {udb_j_str} kr.  
        **Realkredit:** {ydelse_j_str} kr./md.  
        **Ejerudgifter:** {ejer_j_str} kr./md.  
        **Startdepot (År 0):** {depot_j_str} kr.  
        **Mdl. opsparing:** {inv_md_j_str} kr.  
        **Mdl. Udgifter:** {fire_j_str} kr./md.
        """)

    # --- UI: PLACERING OVER TABEL (Ejerudgift & Toggle) ---
    st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
    col_spacer, col_tog, col_ejer = st.columns([0.5, 0.3, 0.2], vertical_alignment="bottom")
    with col_tog:
        st.toggle("Ejerudgift ekskl. 2024-skat", key=f"mangler_skat_{ydelse_key_clean}", on_change=clear_preset)
        if st.session_state.get(f"mangler_skat_{ydelse_key_clean}", False) and boligpris > 0:
            st.markdown(f"<div style='font-size: 0.8em; color: gray; margin-top: -10px; margin-bottom: 5px;'>ℹ️ +{skat_tillaeg} kr./md. tilføjet</div>", unsafe_allow_html=True)
    with col_ejer:
        st.number_input("Ejerudgift (kr./md.)", value=int(ejerudgifter_standard), step=100, key=f"ejer_{ydelse_key_clean}", on_change=clear_preset)
            
    if is_mc:
        mc_view = st.radio("Vælg Monte Carlo Visning", options=["P10 (Worst-case scenarie)", "Median (Forventet scenarie)"], index=1, horizontal=True, key=f"mc_view_solo_{ydelse_key_clean}", label_visibility="collapsed")
        is_worst_case = (mc_view == "P10 (Worst-case scenarie)")
    else:
        is_worst_case = False

    table_data = []
    
    for year in range(0, 26):
        c_age_j = age_j + year
        current_ret = market_returns[year]
        
        # Omlægningsscenarie Logik
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > actual_salgsaar:
            if is_valby:
                if nuvaerende_afdragsfri:
                    if oml_aar <= 10:
                        afdraget_beloeb = 0
                    else:
                        mdr_tilbage_ved_10 = (27 - 10) * 12
                        ny_valby_ydelse = valby_fast_restgaeld * (0.002 * (1.002)**mdr_tilbage_ved_10) / ((1.002)**mdr_tilbage_ved_10 - 1)
                        nyt_afdrag_md = ny_valby_ydelse - 8300
                        afdraget_beloeb = nyt_afdrag_md * 12 * (oml_aar - 10)
                else:
                    afdraget_beloeb = valby_afdrag_md * 12 * oml_aar
                restgaeld_ved_oml = max(0, restgaeld_start - afdraget_beloeb)
            else:
                mdr_gaaet = (oml_aar - actual_salgsaar) * 12
                restgaeld_ved_oml = restgaeld_start * ((1 + oprindelig_rente_mnd)**360 - (1 + oprindelig_rente_mnd)**mdr_gaaet) / ((1 + oprindelig_rente_mnd)**360 - 1)
            
            ny_hovedstol = restgaeld_ved_oml + oml_omk + equity_amt
            mnd_rente_ny = oml_total_rente / 12
            
            if mnd_rente_ny > 0:
                factor = (1 + mnd_rente_ny)**360
                if not oml_afdrag_fri: ny_lån_ydelse = ny_hovedstol * (mnd_rente_ny * factor) / (factor - 1)
                else: ny_lån_ydelse = ny_hovedstol * mnd_rente_ny
            else:
                ny_lån_ydelse = ny_hovedstol / 360 if not oml_afdrag_fri else 0.0
                
            renter_md = (ny_hovedstol * oml_total_rente) / 12
            current_ejerudgifter = 3374 * ((1 + global_inflation_rate)**year) if (is_valby and year <= actual_salgsaar) else effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
            
            netto_bolig_total = ny_lån_ydelse + current_ejerudgifter - (renter_md * 0.256)
            diff_bolig = bolig_total_current - netto_bolig_total
            start_fire_j -= diff_bolig; start_inv_md_j += diff_bolig
            bolig_total_current = netto_bolig_total
            
            depot_free_j += equity_amt

        # Udløb af nuværende afdragsfrihed i Valby (År 10 chok)
        if is_valby and nuvaerende_afdragsfri and year == 10:
            if not (aktiver_oml and oml_aar <= 10) and (actual_salgsaar == 0 or actual_salgsaar > 10):
                mdr_tilbage = (27 - 10) * 12
                rente_mnd = 0.024 / 12
                ny_valby_ydelse = valby_fast_restgaeld * (rente_mnd * (1 + rente_mnd)**mdr_tilbage) / ((1 + rente_mnd)**mdr_tilbage - 1)
                ekstra_nominel_ydelse = ny_valby_ydelse - 8300
                valby_afdrag_md = ekstra_nominel_ydelse
                
                start_fire_j += ekstra_nominel_ydelse
                start_inv_md_j -= (ekstra_nominel_ydelse / ((1 + global_inflation_rate)**year))
                bolig_total_current += (ekstra_nominel_ydelse / ((1 + global_inflation_rate)**year))

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate)
            
            if actual_salgsaar > 0 and year <= actual_salgsaar:
                valby_pris_stigning = valby_pris * global_bolig_inflation
                maal_pris_stigning = maal_pris * global_bolig_inflation
                asymmetrisk_gevinst = valby_pris_stigning - maal_pris_stigning
                
                valby_pris += valby_pris_stigning
                maal_pris += maal_pris_stigning
                locked_frivaerdi_j += (valby_afdrag_md * 12) + asymmetrisk_gevinst
                
                if year == actual_salgsaar:
                    skaleret_udbetaling_j = udbetaling_j * (maal_pris / boligpris)
                    fakt_udb_j = min(skaleret_udbetaling_j, locked_frivaerdi_j)
                    depot_free_j += max(0, locked_frivaerdi_j - fakt_udb_j)
                    
                    ny_ydelse = realkreditydelse_netto * (maal_pris / boligpris)
                    ny_ejerudgifter = effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
                    ny_bolig_total = ny_ydelse + ny_ejerudgifter
                    
                    diff_bolig = (bolig_total_current * ((1 + global_inflation_rate)**year)) - ny_bolig_total
                    start_fire_j -= diff_bolig
                    start_inv_md_j += (diff_bolig / ((1 + global_inflation_rate)**year))
                    
                    bolig_total_current = ny_bolig_total / ((1 + global_inflation_rate)**year)
                    restgaeld_start = maal_pris - fakt_udb_j

            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            return_frie_j = depot_free_j * current_ret
            tax_j = np.where(return_frie_j <= prog_limit_j, return_frie_j * 0.27, prog_limit_j * 0.27 + (return_frie_j - prog_limit_j) * 0.42)
            
            depot_free_j = np.maximum(0, depot_free_j + (return_frie_j - tax_j))
            depot_ask_j = np.maximum(0, depot_ask_j * (1 + current_ret * 0.83))
            depot_free_j += np.where(~j_reached_arr, start_inv_md_j * 12 * ((1 + global_inflation_rate)**year), 0)

            ask_limit_year = ask_base_limit * ((1 + global_inflation_rate)**year)
            space_j = np.maximum(0, ask_limit_year - depot_ask_j); move_j = np.minimum(space_j, np.maximum(0, depot_free_j))
            depot_ask_j += move_j; depot_free_j -= move_j
            
            pension_j_current = np.maximum(0, pension_j_current * (1 + (current_ret * (1 - pal_tax))))
            pension_j_current += np.where(~j_reached_arr, st.session_state["pension_indb_j"] * 12 * ((1 + global_inflation_rate)**year), 0)

        p_j = calculate_drawdown_monthly_income(np.maximum(0, depot_ask_j + depot_free_j), c_age_j, pensionsalder_j, global_return_rate_net_drawdown, global_inflation_rate, use_real_drawdown)
        h_j_array = np.maximum(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        j_reached_arr = j_reached_arr | (h_j_array <= 0)

        if n_sims > 1:
            med_dep_j = np.median(depot_ask_j + depot_free_j); p10_dep_j = np.percentile(depot_ask_j + depot_free_j, 10)
            med_p_j = np.median(p_j); p10_p_j = np.percentile(p_j, 10)
            med_h_j = np.median(h_j_array); p90_h_j = np.percentile(h_j_array, 90)
            succ_j = np.mean(h_j_array <= 0) * 100

            if is_worst_case:
                table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{p10_dep_j/1e6:.2f}", "Passiv Indkomst (kr)": format_dkk(p10_p_j), "Arbejdstid (Barista)": f"{get_emoji_status(p90_h_j).split()[0]} {p90_h_j:.1f}t", "Succesrate": f"{succ_j:.0f}%"})
            else:
                table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{med_dep_j/1e6:.2f}", "Passiv Indkomst (kr)": format_dkk(med_p_j), "Arbejdstid (Barista)": get_emoji_status(med_h_j), "Succesrate": f"{succ_j:.0f}%"})
        else:
            table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{(depot_ask_j[0] + depot_free_j[0])/1e6:.2f}", "Passiv Indkomst (kr)": format_dkk(p_j[0]), "Arbejdstid (Barista)": get_emoji_status(h_j_array[0])})
            if j_reached_arr[0]: break

    st.table(pd.DataFrame(table_data).set_index("År"))
    st.write("")
    
    if is_valby or actual_salgsaar > 0:
        st.markdown("### 🔒 Styring af nuværende Valby lån")
        st.toggle("Aktiver afdragsfrihed på nuværende lån (Valby)", key=f"nuvaerende_afdragsfri_{ydelse_key_clean}", on_change=clear_preset, help="Fjerner afdraget på 6.930 kr. fra budgettet, men udløser et komprimeret afdragschok i år 11.")

    with st.expander("🔄 Scenarie for Omlægning (Nyt lån)", expanded=False):
        st.toggle("Aktiver omlægningsscenarie", value=False, key=f"aktiver_oml_{ydelse_key_clean}", on_change=clear_preset)
        col_o1, col_o2, col_o3 = st.columns(3)
        col_o1.number_input("År for omlægning (0-10)", min_value=0, max_value=10, value=5, key=f"oml_aar_{ydelse_key_clean}", on_change=clear_preset)
        col_o2.number_input("Ny rente (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1, key=f"oml_rente_{ydelse_key_clean}", on_change=clear_preset)
        col_o3.number_input("Nyt bidrag (%)", min_value=0.0, max_value=5.0, value=0.45, step=0.05, key=f"oml_bidrag_{ydelse_key_clean}", on_change=clear_preset)
        col_o4, col_o5 = st.columns(2)
        col_o4.toggle("Afdragsfrihed aktiveret på nyt lån", value=True, key=f"oml_afdrag_fri_{ydelse_key_clean}", on_change=clear_preset)
        col_o5.number_input("Omkostninger (kr)", value=50000, step=5000, key=f"oml_omk_{ydelse_key_clean}", on_change=clear_preset)
        
        st.markdown("##### Friværdinedsparing")
        st.toggle("Hæv friværdi til investering", value=False, key=f"use_equity_{ydelse_key_clean}", on_change=clear_preset)
        if st.session_state.get(f"use_equity_{ydelse_key_clean}", False):
            st.number_input("Beløb til aktiedepot (kr.)", min_value=0, value=1000000, step=100000, key=f"equity_amount_{ydelse_key_clean}", on_change=clear_preset)

# --- NAVIGATION KØRSEL ---
if view_selection == "⚙️ Basisdata & Opsætning":
    st.subheader("Konfiguration af personlig økonomi")
    
    st.markdown("### 🛒 Fælles Udgifter & Nuværende Bolig")
    col_mad1, col_mad2, col_valby = st.columns(3)
    with col_mad1:
        st.session_state["mad_total_val"] = st.number_input("Samlet månedligt madbudget (kr.)", min_value=0, value=st.session_state["mad_total_val"], step=500, key="total_mad_input", on_change=clear_preset)
    with col_mad2:
        st.session_state["mad_j_val"] = st.slider("Johans andel af madbudgettet", min_value=0, max_value=int(st.session_state["mad_total_val"]), value=min(st.session_state["mad_j_val"], int(st.session_state["mad_total_val"])), step=100, key="mad_slider_j", on_change=clear_preset)
    with col_valby:
        st.session_state["valby_pris_input"] = st.number_input("Nuværende boligværdi (Valby kr.)", min_value=0, value=st.session_state["valby_pris_input"], step=50000, key="valby_pris_inp", on_change=clear_preset)
        
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
        st.session_state["use_bsu_m"] = st.toggle("Inddrag Norsk BSU", value=st.session_state.get("use_bsu_m", False), key="toggle_bsu_m", on_change=clear_preset)

else:
    is_solo_mode = False
    if st.session_state.get("secret_id", "").strip().lower() == "solo": is_solo_mode = True
    try:
        if "mode" in st.query_params and st.query_params["mode"] == "solo": is_solo_mode = True
    except: pass

    tab_names = ["3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby"]
    if is_solo_mode: tab_names.extend(["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"])
    
    tabs = st.tabs(tab_names)

    with tabs[0]: simulate_joint_fire_plan("3.5M", 3500000, 966000, 434000, 8516, "yd35", 4500, True)
    with tabs[1]: simulate_joint_fire_plan("4.0M", 4000000, 1846222, 1153888, 4075, "yd40", 4500, True)
    with tabs[2]: simulate_joint_fire_plan("4.5M", 4500000, 2250000, 1125000, 4576, "yd45", 4500, True)
    with tabs[3]: simulate_joint_fire_plan("5.0M", 5000000, 2408888, 983888, 6519, "yd50", 4500, True)
    with tabs[4]: simulate_joint_fire_plan("5.5M", 5500000, 1515000, 685000, 13659, "yd55", 4500, True)
    with tabs[5]: simulate_joint_fire_plan("Valby", 6700000, 0, 0, 15230, "ydvb", 3374, False)

    if is_solo_mode:
        with tabs[6]: simulate_solo_fire_plan("3.0M", 3000000, 1200000, 7308, "yds30", 4500)
        with tabs[7]: simulate_solo_fire_plan("3.5M", 3500000, 1400000, 8516, "yds35", 4500)
        with tabs[8]: simulate_solo_fire_plan("4.0M", 4000000, 1600000, 9724, "yds40", 4500)
