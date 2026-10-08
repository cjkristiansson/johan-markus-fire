import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib.parse

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

# --- GOOGLE SHEETS AUTO-SYNC (KUN FOR JOHAN) ---
def clean_currency(x):
    if isinstance(x, str):
        x = x.replace('kr', '').replace('.', '').replace(',', '.').replace(' ', '').strip()
        try: return float(x)
        except: return 0.0
    return float(x) if pd.notnull(x) else 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_google_sheets_data():
    sheet_id = "19kuzhNztBR00hvXMvpE18B0-B5CdoQx2y5JPCcVziPE"
    
    data = {"ask": 190165, "frie": 144591, "forbrug": 89589, "frivaerdi": 2514000}
    success = False
    error_msg = ""
    
    try:
        tab1 = urllib.parse.quote("Saldo")
        url1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={tab1}"
        df1 = pd.read_csv(url1, on_bad_lines='skip')
        
        for c in range(len(df1.columns) - 1):
            for r in range(len(df1)):
                val_lower = str(df1.iloc[r, c]).lower().strip()
                if "på forbrugskonti" in val_lower:
                    val = clean_currency(df1.iloc[r, c + 1])
                    if val > 0: data["forbrug"] = int(val)

        tab2 = urllib.parse.quote("Likviditet, Fonder mm.")
        url2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={tab2}"
        df2 = pd.read_csv(url2, on_bad_lines='skip')
        
        valby_k = 0; valby_a = 0; valby_f = 0
        for c in range(len(df2.columns) - 1):
            for r in range(len(df2)):
                val_lower = str(df2.iloc[r, c]).lower().strip()
                if "investeringar aktiesparkonto" in val_lower:
                    val = clean_currency(df2.iloc[r, c + 1])
                    if val > 0: data["ask"] = int(val)
                elif "investeringar månedsopsparing" in val_lower:
                    val = clean_currency(df2.iloc[r, c + 1])
                    if val > 0: data["frie"] = int(val)
                elif "kontantindsats valby" in val_lower:
                    valby_k = clean_currency(df2.iloc[r, c + 1])
                elif "avbetalat boliglån" in val_lower:
                    valby_a = clean_currency(df2.iloc[r, c + 1])
                elif "friværdi efter salgt" in val_lower:
                    valby_f = clean_currency(df2.iloc[r, c + 1])
        
        tot_frivaerdi = valby_k + valby_a + valby_f
        if tot_frivaerdi > 0: data["frivaerdi"] = int(tot_frivaerdi)
        
        success = True
    except Exception as e:
        error_msg = str(e)
    
    return data, success, error_msg

# INITIALISERING AF SYNC (Johan's data)
if "gsheets_synced" not in st.session_state:
    fetched_data, is_success, err_msg = fetch_google_sheets_data()
    st.session_state["basis_ask_j"] = fetched_data["ask"]
    st.session_state["basis_frie_j"] = fetched_data["frie"]
    st.session_state["forbrugskonti_j"] = fetched_data["forbrug"]
    st.session_state["frivaerdi_j"] = fetched_data["frivaerdi"]
    st.session_state["gsheets_synced"] = True

# --- INITIALISERING AF SESSION STATE (BASISDATA) ---
if "inkomst_j" not in st.session_state: st.session_state["inkomst_j"] = 38468
if "inkomst_m" not in st.session_state: st.session_state["inkomst_m"] = 32983
if "pension_j" not in st.session_state: st.session_state["pension_j"] = 845000
if "pension_m" not in st.session_state: st.session_state["pension_m"] = 570000
if "pension_indb_j" not in st.session_state: st.session_state["pension_indb_j"] = 7500
if "pension_indb_m" not in st.session_state: st.session_state["pension_indb_m"] = 5000

# Formue før boligkøb
if "forbrugskonti_j" not in st.session_state: st.session_state["forbrugskonti_j"] = 89589
if "frivaerdi_j" not in st.session_state: st.session_state["frivaerdi_j"] = 2514000
if "cash_m_base" not in st.session_state: st.session_state["cash_m_base"] = 1153888
if "basis_ask_j" not in st.session_state: st.session_state["basis_ask_j"] = 190165
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 144591
if "basis_ask_m" not in st.session_state: st.session_state["basis_ask_m"] = 170000
if "basis_frie_m" not in st.session_state: st.session_state["basis_frie_m"] = 0

# Toggles og Fælles variabler
if "use_bsu_m" not in st.session_state: st.session_state["use_bsu_m"] = False
if "use_real_drawdown" not in st.session_state: st.session_state["use_real_drawdown"] = False
if "use_ask_500k" not in st.session_state: st.session_state["use_ask_500k"] = False
if "mc_active" not in st.session_state: st.session_state["mc_active"] = True

# Valby Pris Input
if "valby_pris_input" not in st.session_state: st.session_state["valby_pris_input"] = 6600000

# Personlige budgetter - I DAG
if "budget_idag_j" not in st.session_state:
    st.session_state["budget_idag_j"] = {"Mad": 6000, "Renovering": 1000, "A_kasse_Fagforening": 672, "Internet": 0, "Ferie": 1500, "Puregym": 279, "Forsikringer": 170, "Transport": 730, "Frisoer": 450, "Toej": 1200, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Oevrig": 0}
if "budget_idag_m" not in st.session_state:
    st.session_state["budget_idag_m"] = {"Studielaan": 1600, "Mad": 0, "Renovering": 1000, "A_kasse_Fagforening": 520, "Internet": 0, "Ferie": 1500, "Puregym": 0, "Forsikringer": 170, "Transport": 500, "Frisoer": 450, "Toej": 1200, "Telefon": 300, "Streaming": 565, "Charity": 100, "Oevrig": 3000}

# Personlige budgetter - BARISTA FIRE
if "budget_fire_j" not in st.session_state:
    st.session_state["budget_fire_j"] = {"Mad": 3000, "Renovering": 1000, "A_kasse_Fagforening": 542, "Internet": 100, "Ferie": 1500, "Puregym": 279, "Forsikringer": 170, "Transport": 730, "Frisoer": 450, "Toej": 1200, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Oevrig": 2000}
if "budget_fire_m" not in st.session_state:
    st.session_state["budget_fire_m"] = {"Studielaan": 1600, "Mad": 3000, "Renovering": 1000, "A_kasse_Fagforening": 520, "Internet": 0, "Ferie": 1500, "Puregym": 0, "Forsikringer": 170, "Transport": 500, "Frisoer": 450, "Toej": 1200, "Telefon": 300, "Streaming": 565, "Charity": 100, "Oevrig": 3000}

# --- POP-UP MODAL TIL REGLER OG LOGIK ---
@st.dialog("📜 Modellens Regler & Logik")
def show_rules_dialog():
    st.markdown("""
    * **Phantom Withdrawal:** Modellen trækker nu dine årlige passive udgifter konkret fra depoterne hvert simulerede år i Barista-fasen. 
    * **Frie Midler (Realisationsbeskatning):** Skat trækkes ikke af afkastet hvert år, men beregnes først ud fra 27/42% zonerne på de realiserede gevinster ved udbetaling.
    * **Pensions-overgang:** Frem til 67 år finansieres du af Bridge-midler (Frie+ASK). Fra 67-90 år indgår den officielle pension som et aktiv i den passive udbetaling uden at droppe til 0.
    * **Monte Carlo (SORR):** Fordi midler rent faktisk trækkes ud, rammes du realistisk af sequence-of-return-risks (SORR) ved dårlige afkast.
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

st.sidebar.toggle("Købekraftsjusteret udtræk i FIRE-fasen", key="use_real_drawdown", help="Tvinger modellen til at reservere en del af aktieafkastet til at beskytte hovedstolen mod inflation.", on_change=clear_preset)

st.sidebar.divider()
st.sidebar.markdown("### Tidslinje for overgang")
global_years_to_barista = st.sidebar.number_input("År indtil Barista FIRE (Fuldtidsopsparing)", min_value=0, max_value=20, value=0, step=1, help="0 = I skifter i dag. 3 = I arbejder fuldtid i 3 år endnu og sætter overskud til side, inden I trækker jer og begynder at hæve.")

st.sidebar.divider()
st.sidebar.markdown("### Monte Carlo Simulering")
mc_volatility = st.sidebar.slider("Markedsvolatilitet (%)", min_value=5.0, max_value=25.0, value=15.0, step=1.0, on_change=clear_preset) / 100
mc_btn_label = "Slå Monte Carlo FRA" if st.session_state.get("mc_active", False) else "Beregn Monte Carlo"
st.sidebar.button(mc_btn_label, type="primary", use_container_width=True, on_click=toggle_mc)

st.sidebar.divider()
st.sidebar.markdown("### Salg af Valby-lejlighed")
global_salgsaar = st.sidebar.slider("Salgsår (0 = Sælg nu)", min_value=0, max_value=10, value=0, step=1, on_change=clear_preset)
global_bolig_inflation = st.sidebar.slider("Boligmarkedsvækst (Asymmetrisk gevinst %)", min_value=-10.0, max_value=10.0, value=3.0, step=0.5, on_change=clear_preset) / 100
global_salgsomkostninger = st.sidebar.number_input("Salgsomkostninger (kr.)", min_value=0, max_value=500000, value=150000, step=10000, on_change=clear_preset)

st.sidebar.divider()
st.sidebar.markdown("### Boligfinansiering (Nye boliger)")
global_loan_type = st.sidebar.radio("Lånetype", ["Standard lån (F3 Med afdrag)", "FlexLife (F3 30 år afdragsfri)"], on_change=clear_preset, label_visibility="collapsed")

st.sidebar.divider()
st.sidebar.markdown("### Skattepolitik")
st.sidebar.toggle("Hæv ASK-loft til 500.000 kr.", key="use_ask_500k", on_change=clear_preset)

st.sidebar.divider()
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5, on_change=clear_preset)
pensionsalder_j = st.sidebar.number_input("Johans pensionsalder", min_value=55, max_value=75, value=67, step=1, on_change=clear_preset)
pensionsalder_m = st.sidebar.number_input("Markus' pensionsalder", min_value=55, max_value=75, value=65, step=1, on_change=clear_preset)

st.sidebar.divider()
st.sidebar.text_input("Gendan Scenarie-ID", help="Indtast ID for at indlæse specifik konfiguration.", key="secret_id")

# --- SIKRE HJÆLPEFUNKTIONER ---
def format_dkk(amount):
    try:
        if pd.isna(amount) or np.isnan(amount) or np.isinf(amount): return "0"
        return f"{int(amount):,}".replace(',', '.')
    except:
        return "0"

def calculate_drawdown_monthly_income(depot_bridge_arr, depot_pension_arr, current_age, target_age, net_return_rate, inflation_rate, use_real_rate):
    life_expectancy = 90
    if use_real_rate:
        effective_rate = ((1 + net_return_rate) / (1 + inflation_rate)) - 1
    else:
        effective_rate = net_return_rate
    monthly_rate = effective_rate / 12
    
    # Pre-pension: Lever af Bridge funds frem mod pensionsalder
    if current_age < target_age:
        years_left = target_age - current_age
        months_left = years_left * 12
        if monthly_rate <= 0: return depot_bridge_arr / months_left
        return depot_bridge_arr * (monthly_rate * (1 + monthly_rate)**months_left) / ((1 + monthly_rate)**months_left - 1)
    # Post-pension: Lægger pension oveni og udjævner til alder 90 (fjerner age 67 klippen)
    else:
        months_to_90 = np.maximum(1, (life_expectancy - current_age) * 12)
        total_wealth = depot_bridge_arr + depot_pension_arr
        if monthly_rate <= 0: return total_wealth / months_to_90
        return total_wealth * (monthly_rate * (1 + monthly_rate)**months_to_90) / ((1 + monthly_rate)**months_to_90 - 1)

def get_emoji_status(barista_hours):
    try:
        if pd.isna(barista_hours) or np.isnan(barista_hours) or np.isinf(barista_hours): return "🏁 0.0t"
        if barista_hours <= 0: return "🏁 0.0t"
        elif 0 < barista_hours <= 15: return f"🟡 {barista_hours:.1f}t"
        elif 15 < barista_hours <= 25: return f"🟠 {barista_hours:.1f}t"
        else: return f"🔴 {barista_hours:.1f}t"
    except:
        return "🏁 0.0t"

# --- DYNAMISKE SIMULERINGSFUNKTIONER ---
def simulate_joint_fire_plan(scenario_name, boligpris, ydelse_key, ejerudgifter_standard, bolig_solgt):
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

    is_mc = st.session_state.get("mc_active", False)
    n_sims = 1000 if is_mc else 1
    vol = mc_volatility if is_mc else 0.0
    market_returns = np.random.normal(loc=global_return_rate_gross, scale=vol, size=(26, n_sims))

    is_valby = "Valby" in scenario_name
    actual_salgsaar = 0 if is_valby else global_salgsaar
    valby_pris = st.session_state.get("valby_pris_input", 6600000)
    maal_pris = boligpris

    use_bsu = st.session_state.get("use_bsu_m", False)
    bsu_amount = 292060
    
    total_cash_j = st.session_state.get("forbrugskonti_j", 0) + st.session_state.get("frivaerdi_j", 0)
    cash_j = total_cash_j if bolig_solgt else 0
    cash_m = st.session_state["cash_m_base"] if bolig_solgt else 0

    if bolig_solgt and actual_salgsaar == 0:
        cash_j = max(0, cash_j - (global_salgsomkostninger / 2))
        cash_m = max(0, cash_m - (global_salgsomkostninger / 2))
    
    valby_fast_restgaeld = 3059064
    valby_afdrag_md = 0 if nuvaerende_afdragsfri else 6930
    
    if is_valby:
        target_total_udb = 0
        ui_cash_pct, ui_loan_pct = 0, 0
        loan_amt = valby_fast_restgaeld
        effektiv_realkreditydelse_default = 15230
    else:
        target_total_udb = boligpris * 0.60
        ui_cash_pct, ui_loan_pct = 60, 40
        loan_amt = boligpris * 0.40
        r_total = (0.0341 + 0.0045) / 12
        brutto_md = loan_amt * (r_total * (1 + r_total)**360) / ((1 + r_total)**360 - 1)
        effektiv_realkreditydelse_default = int(brutto_md - (loan_amt * r_total * 0.256))

    with st.expander("🏠 Vis økonomiske detaljer & lån", expanded=False):
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")
        with col_inp:
            udb_str = f"{target_total_udb/1e6:g}".replace('.', ',')
            st.markdown(f"<p style='margin-bottom: 15px; margin-top: 0; line-height: 1.3;'>Mål: {int(ui_cash_pct)}% udb. ({udb_str}M) <br> {int(ui_loan_pct)}% lån</p>", unsafe_allow_html=True)
            if is_valby:
                realkreditydelse_netto = st.number_input("Realkreditydelse", value=effektiv_realkreditydelse_default, step=100, key=ydelse_key, on_change=clear_preset)
                effektiv_realkreditydelse = max(0, realkreditydelse_netto - 6930) if nuvaerende_afdragsfri else realkreditydelse_netto
            else:
                if global_loan_type == "FlexLife (F3 30 år afdragsfri)":
                    brutto_md = (loan_amt * (0.0341 + 0.0055)) / 12
                    effektiv_realkreditydelse = brutto_md * (1 - 0.256)
                else:
                    effektiv_realkreditydelse = st.number_input("Manuel ydelse (kr./md.)", value=effektiv_realkreditydelse_default, step=100, key=ydelse_key, on_change=clear_preset, label_visibility="collapsed")

    if actual_salgsaar == 0:
        bsu_passive = 0 if (use_bsu and bolig_solgt) else (983 if use_bsu else 0)
        if use_bsu and bolig_solgt: cash_m += bsu_amount
            
        total_avail_cash = cash_j + cash_m
        if total_avail_cash > 0:
            udbetaling_j_total = target_total_udb * (cash_j / total_avail_cash)
            udbetaling_m_total = target_total_udb * (cash_m / total_avail_cash)
        else:
            udbetaling_j_total = target_total_udb / 2
            udbetaling_m_total = target_total_udb / 2
            
        mangler_m = max(0, udbetaling_m_total - cash_m)
        faktisk_udbetaling_m = udbetaling_m_total - mangler_m
        udbetaling_j_total += mangler_m
        faktisk_udbetaling_j = udbetaling_j_total - max(0, udbetaling_j_total - cash_j)

        base_frie_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        base_frie_m = st.session_state["basis_frie_m"] + (cash_m - faktisk_udbetaling_m)
        
        bolig_faelles_current = (effektiv_realkreditydelse + effektiv_ejerudgift) / 2
        restgaeld_start = valby_fast_restgaeld if is_valby else loan_amt
        locked_frivaerdi_j, locked_frivaerdi_m = 0.0, 0.0
    else:
        bsu_passive = 983 if use_bsu else 0
        faktisk_udbetaling_j, faktisk_udbetaling_m = 0, 0
        base_frie_j, base_frie_m = st.session_state["basis_frie_j"], st.session_state["basis_frie_m"]
        valby_ydelse = 15230 - 6930 if nuvaerende_afdragsfri else 15230
        bolig_faelles_current = (valby_ydelse + 3374) / 2
        restgaeld_start = valby_fast_restgaeld
        locked_frivaerdi_j = float(st.session_state.get("forbrugskonti_j", 0) + st.session_state.get("frivaerdi_j", 0))
        locked_frivaerdi_m = float(st.session_state["cash_m_base"])

    depot_free_j = np.full(n_sims, base_frie_j, dtype=float)
    indskud_frie_j = np.full(n_sims, base_frie_j, dtype=float) # TILFØJET: Sporer indskud til Realisationsskat
    depot_free_m = np.full(n_sims, base_frie_m, dtype=float)
    indskud_frie_m = np.full(n_sims, base_frie_m, dtype=float)

    depot_ask_j = np.full(n_sims, st.session_state["basis_ask_j"], dtype=float)
    depot_ask_m = np.full(n_sims, st.session_state["basis_ask_m"], dtype=float)
    pension_j_current = np.full(n_sims, st.session_state["pension_j"], dtype=float)
    pension_m_current = np.full(n_sims, st.session_state["pension_m"], dtype=float)

    space_j_init = np.maximum(0, ask_base_limit - depot_ask_j)
    move_j = np.minimum(space_j_init, np.maximum(0, depot_free_j))
    frac_j = np.where(depot_free_j > 0, move_j / depot_free_j, 0)
    indskud_frie_j -= indskud_frie_j * frac_j
    depot_ask_j += move_j; depot_free_j -= move_j

    space_m_init = np.maximum(0, ask_base_limit - depot_ask_m)
    move_m = np.minimum(space_m_init, np.maximum(0, depot_free_m))
    frac_m = np.where(depot_free_m > 0, move_m / depot_free_m, 0)
    indskud_frie_m -= indskud_frie_m * frac_m
    depot_ask_m += move_m; depot_free_m -= move_m

    with col_inp:
        current_budget_j_total = sum(st.session_state["budget_idag_j"].values())
        current_budget_m_total = sum(st.session_state["budget_idag_m"].values())
        fire_budget_j_total = sum(st.session_state["budget_fire_j"].values())
        fire_budget_m_total = sum(st.session_state["budget_fire_m"].values())

        start_inv_md_j = st.session_state["inkomst_j"] - (current_budget_j_total + bolig_faelles_current)
        start_inv_md_m = st.session_state["inkomst_m"] - (current_budget_m_total + bolig_faelles_current) + bsu_passive
        
        start_fire_j = fire_budget_j_total + bolig_faelles_current
        start_fire_m = sum(v for k, v in st.session_state["budget_fire_m"].items() if k not in ["Studielaan"]) + bolig_faelles_current

        udb_j_str = format_dkk(faktisk_udbetaling_j)
        ydelse_j_str = format_dkk(effektiv_realkreditydelse / 2)
        ejer_j_str = format_dkk(effektiv_ejerudgift / 2)
        depot_j_str = format_dkk(depot_free_j[0] + depot_ask_j[0])
        inv_md_j_str = format_dkk(start_inv_md_j)
        fire_j_str = format_dkk(start_fire_j)

    with col_j:
        st.subheader("JOHAN")
        st.markdown(f"**Mål-Udbetaling:** {udb_j_str} kr. | **Realkredit:** {ydelse_j_str} kr./md. | **Mdl. Udgifter (Fremtid):** {fire_j_str} kr./md.")

    col_mc, col_tog, col_ejer = st.columns([0.5, 0.3, 0.2], vertical_alignment="bottom")
    with col_mc:
        is_worst_case = (st.radio("MC View", ["P10 (Worst-case)", "Median"], index=1, horizontal=True, key=f"mc_{ydelse_key_clean}", label_visibility="collapsed") == "P10 (Worst-case)") if is_mc else False
    with col_tog:
        st.toggle("Ejerudgift ekskl. 2024-skat", key=f"mangler_skat_{ydelse_key_clean}", on_change=clear_preset)
    with col_ejer:
        st.number_input("Ejerudgift", value=int(ejerudgifter_standard), step=100, key=f"ejer_{ydelse_key_clean}", on_change=clear_preset)

    table_data, plt_years, plt_depot_j, plt_hours_j = [], [], [], []
    
    for year in range(0, 26):
        c_age_j, c_age_m = age_j + year, age_m + year
        current_ret = market_returns[year]
        
        # Omlægningsscenarie
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > actual_salgsaar:
            if is_valby:
                afdraget_beloeb = 0 if (nuvaerende_afdragsfri and oml_aar <= 10) else (valby_afdrag_md * 12 * oml_aar)
                restgaeld_ved_oml = max(0, restgaeld_start - afdraget_beloeb)
            else:
                mdr_gaaet = (oml_aar - actual_salgsaar) * 12
                restgaeld_ved_oml = restgaeld_start * ((1 + 0.0341/12)**360 - (1 + 0.0341/12)**mdr_gaaet) / ((1 + 0.0341/12)**360 - 1)
            
            ny_hovedstol = restgaeld_ved_oml + oml_omk + equity_amt
            mnd_rente_ny = oml_total_rente / 12
            ny_lån_ydelse = ny_hovedstol * mnd_rente_ny if oml_afdrag_fri else ny_hovedstol * (mnd_rente_ny * (1+mnd_rente_ny)**360) / ((1+mnd_rente_ny)**360 - 1)
            
            current_ejerudgifter = 3374 * ((1 + global_inflation_rate)**year) if (is_valby and year <= actual_salgsaar) else effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
            netto_bolig_faelles = (ny_lån_ydelse + current_ejerudgifter - ((ny_hovedstol * oml_total_rente / 12) * 0.256)) / 2
            
            diff_faelles = bolig_faelles_current - netto_bolig_faelles
            start_fire_j -= diff_faelles; start_inv_md_j += diff_faelles
            bolig_faelles_current = netto_bolig_faelles
            
            depot_free_j += (equity_amt / 2)
            indskud_frie_j += (equity_amt / 2)
            depot_free_m += (equity_amt / 2)
            indskud_frie_m += (equity_amt / 2)

        if is_valby and nuvaerende_afdragsfri and year == 10:
            if not (aktiver_oml and oml_aar <= 10) and (actual_salgsaar == 0 or actual_salgsaar > 10):
                rente_mnd = 0.024 / 12
                ny_valby_ydelse = valby_fast_restgaeld * (rente_mnd * (1 + rente_mnd)**(17*12)) / ((1 + rente_mnd)**(17*12) - 1)
                ekstra_nominel_ydelse = ny_valby_ydelse - 8300
                start_fire_j += (ekstra_nominel_ydelse / 2); start_inv_md_j -= (ekstra_nominel_ydelse / 2)
                bolig_faelles_current += (ekstra_nominel_ydelse / 2)

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate); start_fire_m *= (1 + global_inflation_rate)
            
            if actual_salgsaar > 0 and year <= actual_salgsaar:
                valby_pris_stigning = valby_pris * global_bolig_inflation
                maal_pris_stigning = maal_pris * global_bolig_inflation
                valby_pris += valby_pris_stigning; maal_pris += maal_pris_stigning
                
                locked_frivaerdi_j += (valby_afdrag_md * 12 / 2) + ((valby_pris_stigning - maal_pris_stigning) / 2)
                locked_frivaerdi_m += (valby_afdrag_md * 12 / 2) + ((valby_pris_stigning - maal_pris_stigning) / 2)
                
                if year == actual_salgsaar:
                    locked_frivaerdi_j = max(0, locked_frivaerdi_j - (global_salgsomkostninger / 2))
                    locked_frivaerdi_m = max(0, locked_frivaerdi_m - (global_salgsomkostninger / 2))
                    skaleret_udb_tot = maal_pris * 0.60; skaleret_loan = maal_pris * 0.40
                    total_frivaerdi = locked_frivaerdi_j + locked_frivaerdi_m
                    
                    skal_udb_j = skaleret_udb_tot * (locked_frivaerdi_j / total_frivaerdi) if total_frivaerdi > 0 else skaleret_udb_tot / 2
                    skal_udb_m = skaleret_udb_tot * (locked_frivaerdi_m / total_frivaerdi) if total_frivaerdi > 0 else skaleret_udb_tot / 2
                    
                    if use_bsu:
                        locked_frivaerdi_m += bsu_amount
                        skal_udb_j -= (bsu_amount / 2); skal_udb_m += (bsu_amount / 2)
                        bsu_passive = 0; start_inv_md_m -= 983
                        
                    mangler_m = max(0, skal_udb_m - locked_frivaerdi_m)
                    fakt_udb_m = skal_udb_m - mangler_m
                    fakt_udb_j = (skal_udb_j + mangler_m) - max(0, (skal_udb_j + mangler_m) - locked_frivaerdi_j)
                    
                    add_j = max(0, locked_frivaerdi_j - fakt_udb_j)
                    add_m = max(0, locked_frivaerdi_m - fakt_udb_m)
                    depot_free_j += add_j; indskud_frie_j += add_j
                    depot_free_m += add_m; indskud_frie_m += add_m
                    
                    if global_loan_type == "FlexLife (F3 30 år afdragsfri)":
                        ny_ydelse = ((skaleret_loan * (0.0341 + 0.0055)) / 12) * (1 - 0.256)
                    else:
                        brutto_md = skaleret_loan * ((0.0386/12) * (1 + 0.0386/12)**360) / ((1 + 0.0386/12)**360 - 1)
                        ny_ydelse = brutto_md - (skaleret_loan * (0.0386/12) * 0.256)
                    
                    ny_bolig_faelles = (ny_ydelse + effektiv_ejerudgift * ((1 + global_inflation_rate)**year)) / 2
                    diff_faelles = (bolig_faelles_current * ((1 + global_inflation_rate)**year)) - ny_bolig_faelles
                    start_fire_j -= diff_faelles; start_inv_md_j += (diff_faelles / ((1 + global_inflation_rate)**year))
                    bolig_faelles_current = ny_bolig_faelles / ((1 + global_inflation_rate)**year)

            # Markedsafkast (INGEN LØBENDE SKAT PÅ FRIE MIDLER)
            depot_free_j = np.maximum(0, depot_free_j * (1 + current_ret))
            depot_free_m = np.maximum(0, depot_free_m * (1 + current_ret))
            
            # ASK (Lagerbeskatning 17%)
            depot_ask_j = np.maximum(0, depot_ask_j * (1 + current_ret * 0.83))
            depot_ask_m = np.maximum(0, depot_ask_m * (1 + current_ret * 0.83))

            # FULDTIDS-FASE (År før Barista FIRE)
            if year < global_years_to_barista:
                if start_inv_md_j > 0:
                    c_j = start_inv_md_j * 12 * ((1 + global_inflation_rate)**year)
                    depot_free_j += c_j; indskud_frie_j += c_j
                if start_inv_md_m > 0:
                    c_m = start_inv_md_m * 12 * ((1 + global_inflation_rate)**year)
                    depot_free_m += c_m; indskud_frie_m += c_m
                    
                pension_j_current += st.session_state["pension_indb_j"] * 12 * ((1 + global_inflation_rate)**year)
                pension_m_current += st.session_state["pension_indb_m"] * 12 * ((1 + global_inflation_rate)**year)

            ask_limit_year = ask_base_limit * ((1 + global_inflation_rate)**year)
            
            space_j = np.maximum(0, ask_limit_year - depot_ask_j)
            move_j = np.minimum(space_j, np.maximum(0, depot_free_j))
            frac_j = np.where(depot_free_j > 0, move_j / depot_free_j, 0)
            indskud_frie_j -= indskud_frie_j * frac_j
            depot_ask_j += move_j; depot_free_j -= move_j

            space_m = np.maximum(0, ask_limit_year - depot_ask_m)
            move_m = np.minimum(space_m, np.maximum(0, depot_free_m))
            frac_m = np.where(depot_free_m > 0, move_m / depot_free_m, 0)
            indskud_frie_m -= indskud_frie_m * frac_m
            depot_ask_m += move_m; depot_free_m -= move_m

            pension_j_current = np.maximum(0, pension_j_current * (1 + (current_ret * (1 - pal_tax))))
            pension_m_current = np.maximum(0, pension_m_current * (1 + (current_ret * (1 - pal_tax))))

        # Calculate Sustainable Drawdown (Glat overgang mellem depoter og pension)
        p_j = calculate_drawdown_monthly_income(depot_ask_j + depot_free_j, pension_j_current, c_age_j, pensionsalder_j, st.session_state.get("slider_drawdown", 3.5)/100, global_inflation_rate, use_real_drawdown)
        p_m_drawdown = calculate_drawdown_monthly_income(depot_ask_m + depot_free_m, pension_m_current, c_age_m, pensionsalder_m, st.session_state.get("slider_drawdown", 3.5)/100, global_inflation_rate, use_real_drawdown)
        p_m_total = p_m_drawdown + bsu_passive

        h_j_array = np.maximum(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)
        h_m_array = np.maximum(0, start_fire_m - p_m_total) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        # BARISTA-FASE WITHDRAWALS (Phantom Withdrawal fix & Realisationsbeskatning)
        if year >= global_years_to_barista:
            # Johan Withdrawal
            annual_withdraw_j = p_j * 12
            rem_withdraw_j = annual_withdraw_j
            if c_age_j >= pensionsalder_j:
                draw_pen_j = np.minimum(pension_j_current, rem_withdraw_j)
                pension_j_current -= draw_pen_j
                rem_withdraw_j -= draw_pen_j
                
            taxable_frac_j = np.where(depot_free_j > 0, np.maximum(0, 1 - indskud_frie_j / depot_free_j), 0)
            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            
            gross_j = rem_withdraw_j
            for _ in range(3): # Iterativ udregning af bruttotrækket for at dække skatten
                realized = gross_j * taxable_frac_j
                tax = np.where(realized <= prog_limit_j, realized * 0.27, prog_limit_j * 0.27 + (realized - prog_limit_j) * 0.42)
                gross_j = rem_withdraw_j + tax
                
            gross_j = np.minimum(gross_j, depot_free_j)
            depot_free_j -= gross_j
            indskud_frie_j -= gross_j * (1 - taxable_frac_j)
            
            real_final_j = gross_j * taxable_frac_j
            tax_final_j = np.where(real_final_j <= prog_limit_j, real_final_j * 0.27, prog_limit_j * 0.27 + (real_final_j - prog_limit_j) * 0.42)
            rem_withdraw_j = np.maximum(0, rem_withdraw_j - (gross_j - tax_final_j))
            depot_ask_j -= np.minimum(depot_ask_j, rem_withdraw_j)

            # Markus Withdrawal
            annual_withdraw_m = p_m_drawdown * 12
            rem_withdraw_m = annual_withdraw_m
            if c_age_m >= pensionsalder_m:
                draw_pen_m = np.minimum(pension_m_current, rem_withdraw_m)
                pension_m_current -= draw_pen_m
                rem_withdraw_m -= draw_pen_m
                
            taxable_frac_m = np.where(depot_free_m > 0, np.maximum(0, 1 - indskud_frie_m / depot_free_m), 0)
            prog_limit_m = 79400 * ((1 + global_inflation_rate)**year)
            
            gross_m = rem_withdraw_m
            for _ in range(3): 
                realized_m = gross_m * taxable_frac_m
                tax_m = np.where(realized_m <= prog_limit_m, realized_m * 0.27, prog_limit_m * 0.27 + (realized_m - prog_limit_m) * 0.42)
                gross_m = rem_withdraw_m + tax_m
                
            gross_m = np.minimum(gross_m, depot_free_m)
            depot_free_m -= gross_m
            indskud_frie_m -= gross_m * (1 - taxable_frac_m)
            
            real_final_m = gross_m * taxable_frac_m
            tax_final_m = np.where(real_final_m <= prog_limit_m, real_final_m * 0.27, prog_limit_m * 0.27 + (real_final_m - prog_limit_m) * 0.42)
            rem_withdraw_m = np.maximum(0, rem_withdraw_m - (gross_m - tax_final_m))
            depot_ask_m -= np.minimum(depot_ask_m, rem_withdraw_m)

        if n_sims > 1:
            if is_worst_case:
                dep_j_val = np.percentile(depot_ask_j + depot_free_j, 10)
                hr_j_val = np.percentile(h_j_array, 90)
                table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{dep_j_val/1e6:.2f}", "J.Passiv (kr)": format_dkk(np.percentile(p_j, 10)), "J.Arbtid": f"{get_emoji_status(hr_j_val).split()[0]} {hr_j_val:.1f}t"})
            else:
                dep_j_val = np.median(depot_ask_j + depot_free_j)
                hr_j_val = np.median(h_j_array)
                table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{dep_j_val/1e6:.2f}", "J.Passiv (kr)": format_dkk(np.median(p_j)), "J.Arbtid": get_emoji_status(hr_j_val)})
        else:
            dep_j_val = depot_ask_j[0] + depot_free_j[0]
            hr_j_val = h_j_array[0]
            table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{dep_j_val/1e6:.2f}", "J.Passiv (kr)": format_dkk(p_j[0]), "J.Arbtid": get_emoji_status(h_j_array[0])})

        plt_years.append(year); plt_depot_j.append(dep_j_val / 1e6); plt_hours_j.append(max(0, hr_j_val))

    st.table(pd.DataFrame(table_data).set_index("År"))

    # RENDERING AF PLOTLY GRAF
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=plt_years, y=plt_depot_j, name="Johans Formue (Mio)", stackgroup='one', fillcolor='rgba(140, 133, 123, 0.6)', line=dict(width=0), hoverinfo='x+y+name'), secondary_y=True)
    fig.add_trace(go.Scatter(x=plt_years, y=plt_hours_j, name="Johan Timer/Uge", mode='lines+markers', line=dict(color='#F25C84', width=3), hoverinfo='x+y+name'), secondary_y=False)

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=0, r=0, t=20, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), font=dict(color="#2c2925"))
    fig.update_yaxes(title_text="Barista Timer", secondary_y=False, showgrid=True, gridcolor='rgba(200, 200, 200, 0.2)', zeroline=False, rangemode='tozero', tickfont=dict(size=14, color="#2c2925"))
    fig.update_yaxes(title_text="Formue (Mio. kr.)", secondary_y=True, showgrid=False, zeroline=False, tickfont=dict(size=14, color="#2c2925"))
    fig.update_xaxes(title_text="År", showgrid=False, zeroline=False, tickmode='linear', dtick=2, tickfont=dict(size=14, color="#2c2925"))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def simulate_solo_fire_plan(scenario_name, boligpris, ydelse_key, ejerudgifter_standard):
    pal_tax, weeks_per_month, age_j = 0.153, 4.33, 41
    ydelse_key_clean = ydelse_key.replace("solo_", "")
    
    nuvaerende_afdragsfri = st.session_state.get(f"nuvaerende_afdragsfri_{ydelse_key_clean}", False)
    mangler_skat = st.session_state.get(f"mangler_skat_{ydelse_key_clean}", False)
    effektiv_ejerudgift = st.session_state.get(f"ejer_{ydelse_key_clean}", int(ejerudgifter_standard)) + (int((boligpris * 0.0055) / 12) if mangler_skat else 0)

    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key_clean}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key_clean}", 5)
    oml_total_rente = st.session_state.get(f"oml_rente_{ydelse_key_clean}", 4.0)/100 + st.session_state.get(f"oml_bidrag_{ydelse_key_clean}", 0.45)/100
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{ydelse_key_clean}", True)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key_clean}", 50000)
    equity_amt = st.session_state.get(f"equity_amount_{ydelse_key_clean}", 1000000) if st.session_state.get(f"use_equity_{ydelse_key_clean}", False) else 0

    use_real_drawdown = st.session_state.get("use_real_drawdown", False)
    ask_base_limit = 500000 if st.session_state.get("use_ask_500k", False) else 174000

    is_mc = st.session_state.get("mc_active", False)
    n_sims = 1000 if is_mc else 1
    market_returns = np.random.normal(loc=global_return_rate_gross, scale=mc_volatility if is_mc else 0.0, size=(26, n_sims))

    is_valby = "Valby" in scenario_name
    actual_salgsaar = 0 if is_valby else global_salgsaar
    
    cash_j = st.session_state.get("forbrugskonti_j", 0) + st.session_state.get("frivaerdi_j", 0)
    if not is_valby and actual_salgsaar == 0: cash_j = max(0, cash_j - global_salgsomkostninger)

    valby_pris = st.session_state.get("valby_pris_input", 6600000)
    maal_pris = boligpris
    valby_fast_restgaeld = 3059064
    valby_afdrag_md = 0 if nuvaerende_afdragsfri else 6930

    if is_valby:
        faktisk_udbetaling_j, loan_amt = 0, valby_fast_restgaeld
        effektiv_realkreditydelse_default = 15230
    else:
        faktisk_udbetaling_j, loan_amt = boligpris * 0.60, boligpris * 0.40
        r_total = (0.0341 + 0.0045) / 12
        brutto_md = loan_amt * (r_total * (1 + r_total)**360) / ((1 + r_total)**360 - 1)
        effektiv_realkreditydelse_default = int(brutto_md - (loan_amt * r_total * 0.256))

    with st.expander("⚙️ Vis økonomiske detaljer & lån", expanded=False):
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")
        with col_inp:
            st.markdown(f"<p style='margin-bottom: 15px;'>Mål: 60% udb. ({faktisk_udbetaling_j/1e6:g}M)</p>", unsafe_allow_html=True)
            if is_valby:
                realkreditydelse_netto = st.number_input("Realkreditydelse", value=effektiv_realkreditydelse_default, step=100, key=ydelse_key, on_change=clear_preset)
                effektiv_realkreditydelse = max(0, realkreditydelse_netto - 6930) if nuvaerende_afdragsfri else realkreditydelse_netto
            else:
                if global_loan_type == "FlexLife (F3 30 år afdragsfri)":
                    effektiv_realkreditydelse = (loan_amt * (0.0341 + 0.0055) / 12) * (1 - 0.256)
                else:
                    effektiv_realkreditydelse = st.number_input("Manuel ydelse", value=effektiv_realkreditydelse_default, step=100, key=ydelse_key, on_change=clear_preset, label_visibility="collapsed")

    if actual_salgsaar == 0:
        base_frie_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        bolig_total_current = effektiv_realkreditydelse + effektiv_ejerudgift
        restgaeld_start = valby_fast_restgaeld if is_valby else loan_amt
        locked_frivaerdi_j = 0.0
    else:
        faktisk_udbetaling_j = 0
        base_frie_j = st.session_state["basis_frie_j"]
        bolig_total_current = (15230 - 6930 if nuvaerende_afdragsfri else 15230) + 3374
        restgaeld_start = valby_fast_restgaeld
        locked_frivaerdi_j = float(cash_j)

    depot_free_j = np.full(n_sims, base_frie_j, dtype=float)
    indskud_frie_j = np.full(n_sims, base_frie_j, dtype=float) # TILFØJET: Sporer indskud
    depot_ask_j = np.full(n_sims, st.session_state["basis_ask_j"], dtype=float)
    pension_j_current = np.full(n_sims, st.session_state["pension_j"], dtype=float)

    space_j_init = np.maximum(0, ask_base_limit - depot_ask_j)
    move_j = np.minimum(space_j_init, np.maximum(0, depot_free_j))
    frac_j = np.where(depot_free_j > 0, move_j / depot_free_j, 0)
    indskud_frie_j -= indskud_frie_j * frac_j
    depot_ask_j += move_j; depot_free_j -= move_j

    with col_inp:
        solo_budget_idag = st.session_state["budget_idag_j"].copy()
        solo_budget_fire = st.session_state["budget_fire_j"].copy()
        
        solo_budget_fire["Internet"] = solo_budget_fire.get("Internet", 0) * 2
        solo_budget_fire["Forsikringer"] = solo_budget_fire.get("Forsikringer", 0) * 2
        solo_budget_idag["Internet"] = 200 if solo_budget_idag.get("Internet", 0) == 0 else solo_budget_idag.get("Internet", 0) * 2
        solo_budget_idag["Forsikringer"] = solo_budget_idag.get("Forsikringer", 0) * 2

        start_inv_md_j = st.session_state["inkomst_j"] - (sum(solo_budget_idag.values()) + bolig_total_current)
        start_fire_j = sum(solo_budget_fire.values()) + bolig_total_current

    with col_j:
        st.subheader("JOHAN (SOLO)")
        st.markdown(f"**Boligpris:** {format_dkk(boligpris)} kr. | **Realkredit:** {format_dkk(effektiv_realkreditydelse)} kr./md. | **Mdl. Udgifter:** {format_dkk(start_fire_j)} kr./md.")

    col_mc, col_tog, col_ejer = st.columns([0.5, 0.3, 0.2], vertical_alignment="bottom")
    with col_mc:
        is_worst_case = (st.radio("Vælg Monte Carlo", ["P10 (Worst-case)", "Median"], index=1, horizontal=True, key=f"mc_solo_{ydelse_key_clean}", label_visibility="collapsed") == "P10 (Worst-case)") if is_mc else False
    with col_tog:
        st.toggle("Ejerudgift ekskl. 2024-skat", key=f"mangler_skat_{ydelse_key_clean}", on_change=clear_preset)
    with col_ejer:
        st.number_input("Ejerudgift", value=int(ejerudgifter_standard), step=100, key=f"ejer_{ydelse_key_clean}", on_change=clear_preset)

    table_data, plt_years, plt_depot_j, plt_hours_j = [], [], [], []
    
    for year in range(0, 26):
        c_age_j = age_j + year
        current_ret = market_returns[year]
        
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > actual_salgsaar:
            if is_valby:
                afdraget_beloeb = 0 if (nuvaerende_afdragsfri and oml_aar <= 10) else (valby_afdrag_md * 12 * oml_aar)
                restgaeld_ved_oml = max(0, restgaeld_start - afdraget_beloeb)
            else:
                mdr_gaaet = (oml_aar - actual_salgsaar) * 12
                restgaeld_ved_oml = restgaeld_start * ((1 + 0.0341/12)**360 - (1 + 0.0341/12)**mdr_gaaet) / ((1 + 0.0341/12)**360 - 1)
            
            ny_hovedstol = restgaeld_ved_oml + oml_omk + equity_amt
            mnd_rente_ny = oml_total_rente / 12
            ny_lån_ydelse = ny_hovedstol * mnd_rente_ny if oml_afdrag_fri else ny_hovedstol * (mnd_rente_ny * (1+mnd_rente_ny)**360) / ((1+mnd_rente_ny)**360 - 1)
            
            current_ejerudgifter = 3374 * ((1 + global_inflation_rate)**year) if (is_valby and year <= actual_salgsaar) else effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
            netto_bolig_total = ny_lån_ydelse + current_ejerudgifter - ((ny_hovedstol * oml_total_rente / 12) * 0.256)
            
            diff_bolig = bolig_total_current - netto_bolig_total
            start_fire_j -= diff_bolig; start_inv_md_j += diff_bolig
            bolig_total_current = netto_bolig_total
            
            depot_free_j += equity_amt
            indskud_frie_j += equity_amt

        if is_valby and nuvaerende_afdragsfri and year == 10:
            if not (aktiver_oml and oml_aar <= 10) and (actual_salgsaar == 0 or actual_salgsaar > 10):
                rente_mnd = 0.024 / 12
                ny_valby_ydelse = valby_fast_restgaeld * (rente_mnd * (1 + rente_mnd)**(17*12)) / ((1 + rente_mnd)**(17*12) - 1)
                ekstra_nominel_ydelse = ny_valby_ydelse - 8300
                start_fire_j += ekstra_nominel_ydelse
                bolig_total_current += (ekstra_nominel_ydelse / ((1 + global_inflation_rate)**year))

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate)
            
            if actual_salgsaar > 0 and year <= actual_salgsaar:
                valby_pris += (valby_pris * global_bolig_inflation)
                maal_pris += (maal_pris * global_bolig_inflation)
                locked_frivaerdi_j += (valby_afdrag_md * 12) + ((valby_pris * global_bolig_inflation) - (maal_pris * global_bolig_inflation))
                
                if year == actual_salgsaar:
                    locked_frivaerdi_j = max(0, locked_frivaerdi_j - global_salgsomkostninger)
                    skaleret_udb_tot, skaleret_loan = maal_pris * 0.60, maal_pris * 0.40
                    
                    add_j = max(0, locked_frivaerdi_j - skaleret_udb_tot)
                    depot_free_j += add_j; indskud_frie_j += add_j
                    
                    ny_ydelse = ((skaleret_loan * (0.0341 + 0.0055)) / 12) * (1 - 0.256) if global_loan_type == "FlexLife (F3 30 år afdragsfri)" else (skaleret_loan * ((0.0386/12) * (1 + 0.0386/12)**360) / ((1 + 0.0386/12)**360 - 1)) - (skaleret_loan * (0.0386/12) * 0.256)
                    ny_bolig_total = ny_ydelse + effektiv_ejerudgift * ((1 + global_inflation_rate)**year)
                    diff_bolig = (bolig_total_current * ((1 + global_inflation_rate)**year)) - ny_bolig_total
                    start_fire_j -= diff_bolig; start_inv_md_j += (diff_bolig / ((1 + global_inflation_rate)**year))
                    bolig_total_current = ny_bolig_total / ((1 + global_inflation_rate)**year)

            # Markedsafkast uden løbende skat på Frie Midler
            depot_free_j = np.maximum(0, depot_free_j * (1 + current_ret))
            depot_ask_j = np.maximum(0, depot_ask_j * (1 + current_ret * 0.83))
            
            # FULDTIDS-FASE
            if year < global_years_to_barista:
                if start_inv_md_j > 0:
                    c_j = start_inv_md_j * 12 * ((1 + global_inflation_rate)**year)
                    depot_free_j += c_j
                    indskud_frie_j += c_j
                pension_j_current += st.session_state["pension_indb_j"] * 12 * ((1 + global_inflation_rate)**year)

            ask_limit_year = ask_base_limit * ((1 + global_inflation_rate)**year)
            space_j = np.maximum(0, ask_limit_year - depot_ask_j)
            move_j = np.minimum(space_j, np.maximum(0, depot_free_j))
            frac_j = np.where(depot_free_j > 0, move_j / depot_free_j, 0)
            indskud_frie_j -= indskud_frie_j * frac_j
            depot_ask_j += move_j; depot_free_j -= move_j
            
            pension_j_current = np.maximum(0, pension_j_current * (1 + (current_ret * (1 - pal_tax))))

        # Calculate Sustainable Drawdown
        p_j = calculate_drawdown_monthly_income(depot_ask_j + depot_free_j, pension_j_current, c_age_j, pensionsalder_j, st.session_state.get("slider_drawdown", 3.5)/100, global_inflation_rate, use_real_drawdown)
        h_j_array = np.maximum(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        # BARISTA-FASE WITHDRAWALS
        if year >= global_years_to_barista:
            rem_withdraw_j = p_j * 12
            
            if c_age_j >= pensionsalder_j:
                draw_pen_j = np.minimum(pension_j_current, rem_withdraw_j)
                pension_j_current -= draw_pen_j
                rem_withdraw_j -= draw_pen_j
                
            taxable_frac_j = np.where(depot_free_j > 0, np.maximum(0, 1 - indskud_frie_j / depot_free_j), 0)
            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            
            gross_j = rem_withdraw_j
            for _ in range(3):
                realized = gross_j * taxable_frac_j
                tax = np.where(realized <= prog_limit_j, realized * 0.27, prog_limit_j * 0.27 + (realized - prog_limit_j) * 0.42)
                gross_j = rem_withdraw_j + tax
                
            gross_j = np.minimum(gross_j, depot_free_j)
            depot_free_j -= gross_j
            indskud_frie_j -= gross_j * (1 - taxable_frac_j)
            
            real_final_j = gross_j * taxable_frac_j
            tax_final_j = np.where(real_final_j <= prog_limit_j, real_final_j * 0.27, prog_limit_j * 0.27 + (real_final_j - prog_limit_j) * 0.42)
            rem_withdraw_j = np.maximum(0, rem_withdraw_j - (gross_j - tax_final_j))
            
            depot_ask_j -= np.minimum(depot_ask_j, rem_withdraw_j)

        if n_sims > 1:
            if is_worst_case:
                dep_j_val = np.percentile(depot_ask_j + depot_free_j, 10)
                hr_j_val = np.percentile(h_j_array, 90)
                table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{dep_j_val/1e6:.2f}", "Passiv Indkomst (kr)": format_dkk(np.percentile(p_j, 10)), "Arbejdstid (Barista)": f"{get_emoji_status(hr_j_val).split()[0]} {hr_j_val:.1f}t"})
            else:
                dep_j_val = np.median(depot_ask_j + depot_free_j)
                hr_j_val = np.median(h_j_array)
                table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{dep_j_val/1e6:.2f}", "Passiv Indkomst (kr)": format_dkk(np.median(p_j)), "Arbejdstid (Barista)": get_emoji_status(hr_j_val)})
        else:
            dep_j_val = depot_ask_j[0] + depot_free_j[0]
            hr_j_val = h_j_array[0]
            table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{dep_j_val/1e6:.2f}", "Passiv Indkomst (kr)": format_dkk(p_j[0]), "Arbejdstid (Barista)": get_emoji_status(h_j_array[0])})
            
        plt_years.append(year); plt_depot_j.append(dep_j_val / 1e6); plt_hours_j.append(max(0, hr_j_val))

    st.table(pd.DataFrame(table_data).set_index("År"))

    # RENDERING AF PLOTLY GRAF (SOLO)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=plt_years, y=plt_depot_j, name="Johans Formue (Mio)", stackgroup='one', fillcolor='rgba(140, 133, 123, 0.6)', line=dict(width=0), hoverinfo='x+y+name'), secondary_y=True)
    fig.add_trace(go.Scatter(x=plt_years, y=plt_hours_j, name="Johan Timer/Uge", mode='lines+markers', line=dict(color='#F25C84', width=3), hoverinfo='x+y+name'), secondary_y=False)

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=0, r=0, t=20, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), font=dict(color="#2c2925"))
    fig.update_yaxes(title_text="Barista Timer", secondary_y=False, showgrid=True, gridcolor='rgba(200, 200, 200, 0.2)', zeroline=False, rangemode='tozero', tickfont=dict(size=14, color="#2c2925"))
    fig.update_yaxes(title_text="Formue (Mio. kr.)", secondary_y=True, showgrid=False, zeroline=False, tickfont=dict(size=14, color="#2c2925"))
    fig.update_xaxes(title_text="År", showgrid=False, zeroline=False, tickmode='linear', dtick=2, tickfont=dict(size=14, color="#2c2925"))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

else:
    is_solo_mode = (st.session_state.get("secret_id", "").strip().lower() == "solo")
    try:
        if "mode" in st.query_params and st.query_params["mode"] == "solo": is_solo_mode = True
    except: pass

    tab_names = ["3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby"]
    if is_solo_mode: tab_names.extend(["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"])
    
    tabs = st.tabs(tab_names)

    with tabs[0]: simulate_joint_fire_plan("3.5M", 3500000, "yd35", 4500, True)
    with tabs[1]: simulate_joint_fire_plan("4.0M", 4000000, "yd40", 4500, True)
    with tabs[2]: simulate_joint_fire_plan("4.5M", 4500000, "yd45", 4500, True)
    with tabs[3]: simulate_joint_fire_plan("5.0M", 5000000, "yd50", 4500, True)
    with tabs[4]: simulate_joint_fire_plan("5.5M", 5500000, "yd55", 4500, True)
    with tabs[5]: simulate_joint_fire_plan("Valby", 6700000, "ydvb", 3374, False)

    if is_solo_mode:
        with tabs[6]: simulate_solo_fire_plan("3.0M", 3000000, "yds30", 4500)
        with tabs[7]: simulate_solo_fire_plan("3.5M", 3500000, "yds35", 4500)
        with tabs[8]: simulate_solo_fire_plan("4.0M", 4000000, "yds40", 4500)
