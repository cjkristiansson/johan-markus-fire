import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

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

# Personlige budgetter
if "budget_j" not in st.session_state:
    st.session_state["budget_j"] = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1674, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
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
    * **Dynamiske boligudgifter:** Bliver der optaget realkreditlån, indgår ydelsen fuldt ud i de månedlige FIRE-udgifter for det givne scenarie.
    """)

# --- TOP HEADER ---
col_title, col_link = st.columns([0.85, 0.15], vertical_alignment="center")
with col_title:
    st.title("FIRE Brofinansiering")
with col_link:
    if st.button("📜 Regler & Logik", type="tertiary", use_container_width=True):
        show_rules_dialog()


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

st.sidebar.divider()
st.sidebar.text_input("Gendan Scenarie-ID", key="secret_id")


# --- DYNAMISKE SIMULERINGSFUNKTIONER ---
def calculate_drawdown_monthly_income(depot_total, current_age, target_age, net_return_rate):
    if current_age >= target_age: return 0
    years_left = target_age - current_age
    months_left = years_left * 12
    monthly_rate = net_return_rate / 12
    if monthly_rate == 0: return depot_total / months_left
    return depot_total * (monthly_rate * (1 + monthly_rate)**months_left) / ((1 + monthly_rate)**months_left - 1)

def get_emoji_status(barista_hours):
    if barista_hours <= 0: return "🟢 0.0t"
    elif 0 < barista_hours <= 15: return f"🟡 {barista_hours:.1f}t"
    elif 15 < barista_hours <= 25: return f"🟠 {barista_hours:.1f}t"
    else: return f"🔴 {barista_hours:.1f}t"

def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, realkreditydelse_netto, ejerudgifter_total, bolig_solgt):
    pal_tax, weeks_per_month, age_j, age_m = 0.153, 4.33, 41, 32
    cash_j = st.session_state["cash_j_base"] if bolig_solgt else 0
    cash_m = st.session_state["cash_m_base"] if bolig_solgt else 0

    mangler_m = max(0, udbetaling_m - cash_m)
    faktisk_udbetaling_m = udbetaling_m - mangler_m
    udbetaling_j_total = udbetaling_j + mangler_m
    faktisk_udbetaling_j = udbetaling_j_total - max(0, udbetaling_j_total - cash_j)

    depot_free_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
    depot_free_m = st.session_state["basis_frie_m"] + (cash_m - faktisk_udbetaling_m)
    depot_ask_j, depot_ask_m = st.session_state["basis_ask_j"], st.session_state["basis_ask_m"]

    bolig_faelles = (realkreditydelse_netto + ejerudgifter_total) / 2
    start_inv_md_j = st.session_state["inkomst_j"] - (sum(st.session_state["budget_j"].values()) + bolig_faelles)
    start_inv_md_m = st.session_state["inkomst_m"] - (sum(st.session_state["budget_m"].values()) + bolig_faelles)
    start_fire_j = sum(v for k, v in st.session_state["budget_j"].items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_faelles
    start_fire_m = sum(v for k, v in st.session_state["budget_m"].items() if k not in ["A_kasse_Fagforening", "Loensikring", "Studielaan"]) + bolig_faelles

    if max(0, udbetaling_j_total - cash_j) > 0:
        st.error(f"⚠️ ADVARSEL: Udbetalingen overstiger jeres likviditet.")

    st.write("") 

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("JOHAN")
        st.markdown(f"**Udbetaling:** {int(faktisk_udbetaling_j):,} kr. | **Startdepot:** {int(depot_free_j + depot_ask_j):,} kr.")
    with col2:
        st.subheader("MARKUS")
        st.markdown(f"**Udbetaling:** {int(faktisk_udbetaling_m):,} kr. | **Startdepot:** {int(depot_free_m + depot_ask_m):,} kr.")

    st.write("")

    table_data = []
    j_reached, m_reached = False, False
    
    for year in range(0, 26):
        c_age_j, c_age_m = age_j + year, age_m + year
        
        if year > 0:
            start_fire_j *= (1 + global_inflation_rate)
            start_fire_m *= (1 + global_inflation_rate)
            
            # Afkast på primo-beholdning (FØR opsparing tilføjes)
            depot_ask_j *= (1 + global_return_rate_gross * 0.83); depot_free_j *= (1 + global_return_rate_gross * 0.73)
            depot_ask_m *= (1 + global_return_rate_gross * 0.83); depot_free_m *= (1 + global_return_rate_gross * 0.73)
            
            # Tilføj opsparing til sidst
            if not j_reached: depot_free_j += (start_inv_md_j * 12 * ((1 + global_inflation_rate)**year))
            if not m_reached: depot_free_m += (start_inv_md_m * 12 * ((1 + global_inflation_rate)**year))

        p_j = calculate_drawdown_monthly_income(depot_ask_j + depot_free_j, c_age_j, pensionsalder_j, global_return_rate_net_drawdown)
        h_j = max(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)
        p_m = calculate_drawdown_monthly_income(depot_ask_m + depot_free_m, c_age_m, pensionsalder_m, global_return_rate_net_drawdown)
        h_m = max(0, start_fire_m - p_m) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{(depot_ask_j + depot_free_j)/1e6:.2f}", "J.Arbtid": get_emoji_status(h_j), "M.alder": c_age_m, "M.depot (M)": f"{(depot_ask_m + depot_free_m)/1e6:.2f}", "M.Arbtid": get_emoji_status(h_m)})
        if h_j <= 0: j_reached = True
        if h_m <= 0: m_reached = True

    st.table(pd.DataFrame(table_data).set_index("År"))

def simulate_solo_fire_plan(scenario_name, boligpris, udbetaling_j, realkreditydelse_netto, ejerudgifter_total):
    pal_tax, weeks_per_month, age_j = 0.153, 4.33, 41
    cash_j = st.session_state["cash_j_base"]
    faktisk_udbetaling_j = min(udbetaling_j, cash_j)
    depot_free_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
    depot_ask_j = st.session_state["basis_ask_j"]

    solo_budget_j = st.session_state["budget_j"].copy()
    solo_budget_j["Mad"] = 3000
    bolig_total = realkreditydelse_netto + ejerudgifter_total
    start_inv_md_j = st.session_state["inkomst_j"] - (sum(solo_budget_j.values()) + bolig_total)
    start_fire_j = sum(v for k, v in solo_budget_j.items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_total

    st.subheader(f"JOHAN (SOLO: {scenario_name})")
    st.markdown(f"**Boligpris:** {int(boligpris):,} kr. | **Udbetaling:** {int(faktisk_udbetaling_j):,} kr.")
    
    table_data = []
    j_reached = False
    for year in range(0, 26):
        c_age_j = age_j + year
        if year > 0:
            start_fire_j *= (1 + global_inflation_rate)
            depot_ask_j *= (1 + global_return_rate_gross * 0.83); depot_free_j *= (1 + global_return_rate_gross * 0.73)
            if not j_reached: depot_free_j += (start_inv_md_j * 12 * ((1 + global_inflation_rate)**year))

        p_j = calculate_drawdown_monthly_income(depot_ask_j + depot_free_j, c_age_j, pensionsalder_j, global_return_rate_net_drawdown)
        h_j = max(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)
        table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{(depot_ask_j + depot_free_j)/1e6:.2f}", "Arbejdstid": get_emoji_status(h_j)})
        if h_j <= 0: j_reached = True

    st.table(pd.DataFrame(table_data).set_index("År"))

# --- NAVIGATION ---
view_selection = st.pills("Navigation", options=["Boligscenarier", "⚙️ Basisdata & Opsætning"], default="Boligscenarier", label_visibility="collapsed")
if view_selection == "⚙️ Basisdata & Opsætning":
    col_setup_j, col_setup_m = st.columns(2)
    with col_setup_j:
        st.session_state["inkomst_j"] = st.number_input("Johan Løn", value=st.session_state["inkomst_j"])
        df_j = st.data_editor(pd.DataFrame(list(st.session_state["budget_j"].items()), columns=["Kategori", "Beløb"]), key="ed_j")
        st.session_state["budget_j"] = dict(df_j.values)
    with col_setup_m:
        st.session_state["inkomst_m"] = st.number_input("Markus Løn", value=st.session_state["inkomst_m"])
        df_m = st.data_editor(pd.DataFrame(list(st.session_state["budget_m"].items()), columns=["Kategori", "Beløb"]), key="ed_m")
        st.session_state["budget_m"] = dict(df_m.values)
else:
    is_solo_mode = st.session_state.get("secret_id", "").strip().lower() == "solo"
    tab_names = ["3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby"]
    if is_solo_mode: tab_names.extend(["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"])
    tabs = st.tabs(tab_names)
    with tabs[0]: simulate_joint_fire_plan("3.5M", 3500000, 966000, 434000, 8516, 4564, True)
    with tabs[1]: simulate_joint_fire_plan("4.0M", 4000000, 1846222, 1153888, 4075, 4564, True)
    with tabs[2]: simulate_joint_fire_plan("4.5M", 4500000, 2250000, 1125000, 4576, 4564, True)
    with tabs[3]: simulate_joint_fire_plan("5.0M", 5000000, 2408888, 983888, 6519, 4564, True)
    with tabs[4]: simulate_joint_fire_plan("5.5M", 5500000, 1515000, 685000, 13659, 4564, True)
    with tabs[5]: simulate_joint_fire_plan("Valby", 6700000, 0, 0, 15230, 4564, False)
    if is_solo_mode:
        with tabs[6]: simulate_solo_fire_plan("3.0M Solo", 3000000, 1200000, 7308, 3500)
        with tabs[7]: simulate_solo_fire_plan("3.5M Solo", 3500000, 1400000, 8516, 4000)
        with tabs[8]: simulate_solo_fire_plan("4.0M Solo", 4000000, 1600000, 9724, 4500)
