import streamlit as st
import pandas as pd

# Her tvinges sidebaren ud på alle desktop-skærme
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

# Formue før boligkøb
if "cash_j_base" not in st.session_state: st.session_state["cash_j_base"] = 2567500
if "cash_m_base" not in st.session_state: st.session_state["cash_m_base"] = 1153888
if "basis_ask_j" not in st.session_state: st.session_state["basis_ask_j"] = 174000
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 65000
if "basis_ask_m" not in st.session_state: st.session_state["basis_ask_m"] = 170000
if "basis_frie_m" not in st.session_state: st.session_state["basis_frie_m"] = 0

# Toggles (Sikrer default-værdier i session state)
if "use_bsu_m" not in st.session_state: st.session_state["use_bsu_m"] = False
if "use_loensikring_j" not in st.session_state: st.session_state["use_loensikring_j"] = True
if "use_loensikring_m" not in st.session_state: st.session_state["use_loensikring_m"] = True

# Personlige budgetter
if "budget_j" not in st.session_state:
    st.session_state["budget_j"] = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1836, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
if "budget_m" not in st.session_state:
    st.session_state["budget_m"] = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 720, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

# --- POP-UP MODAL TIL REGLER OG LOGIK ---
@st.dialog("📜 Modellens Regler & Logik")
def show_rules_dialog():
    st.markdown("""
    * **Trin 0 (Boligkøb først):** Startdepotet i år 1 er formuen *efter* udbetaling til bolig. Aktiedepoter Låst til FIRE.
    * **Lagerbeskatning:** ASK beskattes fladt med 17%. Frie midler beskattes progressivt (27% op til grænsen, 42% derover). Progressionsgrænsen (79.400 kr. i 2026) indekseres årligt med inflationen.
    * **Inflationseffekt:** Udgifter, opsparingsrate og progressionsgrænser stiger alle med den valgte inflationsrate år for år i modellen.
    * **Pension adskilt:** Pensionsdepoter bruges *ikke* før pensionsalderen nås. Indbetalinger stopper det år fuld FIRE nås, hvorefter depotet kun vokser med afkast minus PAL-skat (15,3%).
    * **Barista-timer:** Timer beregnes på *restbehovet*. Passiv indkomst fra depotet fratrækkes FIRE-udgifterne først.
    * **Dynamiske boligudgifter:** Bliver der optaget realkreditlån, indgår ydelsen fuldt ud i de månedlige FIRE-udgifter for det givne scenarie. Nye boligskatter fordeles 50/50.
    * **Omlægningsscenarie:** Kan aktiveres under tabellerne. Modulet er deaktiveret som standard. Når det slås til, justeres restgæld, rente, afdrag og omkostninger, hvilket giver et nyt månedligt råderum der automatisk geninvesteres.
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
col_preset1, col_preset2 = st.sidebar.columns(2)
use_base = col_preset1.button("Standard", use_container_width=True)
use_conservative = col_preset2.button("Konservativ", use_container_width=True)

if use_conservative:
    st.session_state["preset_return"] = 5.5
    st.session_state["preset_drawdown"] = 3.5
    st.session_state["preset_inflation"] = 2.5
elif use_base:
    st.session_state["preset_return"] = 7.0
    st.session_state["preset_drawdown"] = 4.5
    st.session_state["preset_inflation"] = 2.0

global_return_rate_gross = st.sidebar.slider("Bruttoafkast under opsparing (%)", min_value=3.0, max_value=10.0, value=st.session_state.get("preset_return", 7.0), step=0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast i passiv fase (%)", min_value=2.0, max_value=8.0, value=st.session_state.get("preset_drawdown", 4.5), step=0.1) / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", min_value=0.0, max_value=5.0, value=st.session_state.get("preset_inflation", 2.0), step=0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5)

st.sidebar.divider()
pensionsalder_j = st.sidebar.number_input("Johans pensionsalder", min_value=55, max_value=75, value=67, step=1)
pensionsalder_m = st.sidebar.number_input("Markus' pensionsalder", min_value=55, max_value=75, value=65, step=1)

# DEN HEMMELIGE BAGDØR
st.sidebar.divider()
st.sidebar.text_input("Gendan Scenarie-ID", help="Indtast ID for at indlæse specifik konfiguration.", key="secret_id")

# --- DYNAMISKE SIMULERINGSFUNKTIONER ---
def calculate_drawdown_monthly_income(depot_total, current_age, target_age, net_return_rate):
    if current_age >= target_age: return 0
    years_left = target_age - current_age
    months_left = years_left * 12
    monthly_rate = net_return_rate / 12
    if monthly_rate == 0: return depot_total / months_left
    return depot_total * (monthly_rate * (1 + monthly_rate)**months_left) / ((1 + monthly_rate)**months_left - 1)

def get_emoji_status(barista_hours):
    if barista_hours == 0: return "🏁 0.0t"
    elif 0 < barista_hours <= 15: return f"🟡 {barista_hours:.1f}t"
    elif 15 < barista_hours <= 25: return f"🟠 {barista_hours:.1f}t"
    else: return f"🔴 {barista_hours:.1f}t"

def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, ydelse_default, ydelse_key, ejerudgifter_total, bolig_solgt, boligskat_md):
    pal_tax, weeks_per_month, age_j, age_m = 0.153, 4.33, 41, 32
    
    # Hent state for Omlægningsscenarie
    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{ydelse_key}", 4.0) / 100
    oml_afdrag = st.session_state.get(f"oml_afdrag_{ydelse_key}", True)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key}", 50000)

    # BSU Logik
    use_bsu = st.session_state.get("use_bsu_m", False)
    bsu_amount = 292060
    
    cash_j = st.session_state["cash_j_base"] if bolig_solgt else 0
    cash_m = st.session_state["cash_m_base"] if bolig_solgt else 0
    
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

    if max(0, udbetaling_j_total - cash_j) > 0:
        st.error(f"⚠️ ADVARSEL: Udbetalingen overstiger jeres likviditet.")

    total_udbetaling = faktisk_udbetaling_j + faktisk_udbetaling_m
    cash_pct = (total_udbetaling / boligpris * 100) if boligpris > 0 else 0
    loan_pct = 100 - cash_pct

    # Placer specifikationerne ind i en expander
    with st.expander("🏠 Vis økonomiske detaljer & lån", expanded=False):
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        with col_inp:
            st.markdown(
                f"<p style='margin-bottom: 60px; margin-top: 0; line-height: 1.3;'>"
                f"{int(cash_pct)}% kontantudbetaling ({f'{int(total_udbetaling):,}'.replace(',', '.')} kr.) | {int(loan_pct)}% lån</p>", 
                unsafe_allow_html=True
            )
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key)

        # --- FIRE BEREGNINGER ---
        depot_free_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        depot_free_m = st.session_state["basis_frie_m"] + (cash_m - faktisk_udbetaling_m)
        depot_ask_j, depot_ask_m = st.session_state["basis_ask_j"], st.session_state["basis_ask_m"]

        bolig_faelles = (realkreditydelse_netto + ejerudgifter_total + boligskat_md) / 2
        
        # Håndter lønsikring
        use_loensikring_j = st.session_state.get("use_loensikring_j", True)
        budget_j_total = sum(st.session_state["budget_j"].values())
        if not use_loensikring_j:
            budget_j_total -= st.session_state["budget_j"].get("Loensikring", 0)

        use_loensikring_m = st.session_state.get("use_loensikring_m", True)
        budget_m_total = sum(st.session_state["budget_m"].values())
        if not use_loensikring_m:
            budget_m_total -= st.session_state["budget_m"].get("Loensikring", 0)

        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_faelles)
        start_inv_md_m = st.session_state["inkomst_m"] - (budget_m_total + bolig_faelles) + bsu_passive
        
        start_fire_j = sum(v for k, v in st.session_state["budget_j"].items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_faelles
        start_fire_m = sum(v for k, v in st.session_state["budget_m"].items() if k not in ["A_kasse_Fagforening", "Loensikring", "Studielaan"]) + bolig_faelles

        skat_line_j = f"**Boligskat (egen andel):** {f'{int(boligskat_md / 2):,}'.replace(',', '.')} kr./md.  \n" if boligskat_md > 0 else ""
        skat_line_m = f"**Boligskat (egen andel):** {f'{int(boligskat_md / 2):,}'.replace(',', '.')} kr./md.  \n" if boligskat_md > 0 else ""

        with col_j:
            st.subheader(f"JOHAN")
            st.markdown(f"""
            **Udbetaling:** {f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.  
            **Realkreditydelse:** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.  
            {skat_line_j}**Startdepot:** {f'{int(depot_free_j + depot_ask_j):,}'.replace(',', '.')} kr.  
            **Mdl. opsparing:** {f'{int(start_inv_md_j):,}'.replace(',', '.')} kr.  
            **Mdl. Udgifter:** {f'{int(start_fire_j):,}'.replace(',', '.')} kr./md.
            """)
        
        with col_m:
            st.subheader(f"MARKUS")
            st.markdown(f"""
            **Udbetaling:** {f'{int(faktisk_udbetaling_m):,}'.replace(',', '.')} kr.  
            **Realkreditydelse:** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.  
            {skat_line_m}**Startdepot:** {f'{int(depot_free_m + depot_ask_m):,}'.replace(',', '.')} kr.  
            **Mdl. opsparing:** {f'{int(start_inv_md_m):,}'.replace(',', '.')} kr.  
            **Mdl. Udgifter:** {f'{int(start_fire_m):,}'.replace(',', '.')} kr./md.
            """)

    st.write("") 

    restgaeld = boligpris - total_udbetaling
    bolig_faelles_current = bolig_faelles

    table_data = []
    j_reached, m_reached = False, False
    j_fire_age, m_fire_age = 0, 0
    pension_at_target_j, pension_at_target_m = 0, 0
    
    for year in range(0, 26):
        c_age_j, c_age_m = age_j + year, age_m + year
        
        # Anvend omlægning hvis aktiveret i UI
        if aktiver_oml and year == oml_aar and boligpris > 0:
            restgaeld += oml_omk
            mnd_rente_f = oml_rente / 12
            
            if oml_afdrag:
                ny_ydelse = restgaeld * (mnd_rente_f * (1 + mnd_rente_f)**360) / ((1 + mnd_rente_f)**360 - 1)
            else:
                ny_ydelse = restgaeld * mnd_rente_f
                
            renter_md = (restgaeld * oml_rente) / 12
            netto_bolig_faelles = (ny_ydelse + ejerudgifter_total + boligskat_md - (renter_md * 0.256)) / 2
