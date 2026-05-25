import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

# --- INDLÆS EKSTERN CSS ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Kunne ikke finde {file_name}. Sørg for at filen ligger i samme mappe som app.py.")

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
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 71000
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
    * **Risiko - Inflation på udgifter:** FIRE-udgifterne fremskrives med 2% årligt. Nominelle kroner undervurderer systematisk fremtidige udgifter — 10.000 kr./måned i dag svarer til ca. 14.900 kr./måned om 20 år ved 2% inflation.
    * **Risiko - Folkepensionsmodregning:** Folkepension og pensionstillæg medregnes fra pensionsalderen, men pensionstillægget reduceres ved formue og øvrig indkomst. Ved større depoter kan det effektive tillæg være markant lavere end grundbeløbet — modellen anvender et konservativt skøn.
    """)

# --- TOP HEADER (TITEL OG KNAP PÅ PRÆCIS SAMME LINJE) ---
col_title, col_link = st.columns([0.85, 0.15], vertical_alignment="center")
with col_title:
    st.title("FIRE Brofinansiering")
with col_link:
    if st.button("📜 Regler & Logik", type="tertiary", use_container_width=True):
        show_rules_dialog()


# --- 1. SIDEBAR TIL INTERAKTIVE VARIABLER ---
st.sidebar.header("Globale Antagelser")
st.sidebar.markdown("Juster variablerne for at stress-teste alle scenarier samtidigt.")

# --- PRESET KNAPPER ---
col_preset1, col_preset2 = st.sidebar.columns(2)
use_base = col_preset1.button("Standard", use_container_width=True, help="Afkast 7% / Drawdown 4,5% / Inflation 2%")
use_conservative = col_preset2.button("Konservativ", use_container_width=True, help="Afkast 5,5% / Drawdown 3,5% / Inflation 2,5%")

if use_conservative:
    st.session_state["preset_return"] = 5.5
    st.session_state["preset_drawdown"] = 3.5
    st.session_state["preset_inflation"] = 2.5
elif use_base:
    st.session_state["preset_return"] = 7.0
    st.session_state["preset_drawdown"] = 4.5
    st.session_state["preset_inflation"] = 2.0

default_return = st.session_state.get("preset_return", 7.0)
default_drawdown = st.session_state.get("preset_drawdown", 4.5)
default_inflation = st.session_state.get("preset_inflation", 2.0)

global_return_rate_gross = st.sidebar.slider("Bruttoafkast under opsparing (%)", min_value=3.0, max_value=10.0, value=default_return, step=0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast i passiv fase (%)", min_value=2.0, max_value=8.0, value=default_drawdown, step=0.1) / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", min_value=0.0, max_value=5.0, value=default_inflation, step=0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5)

st.sidebar.divider()
st.sidebar.markdown("### Pensionsalder")
pensionsalder_j = st.sidebar.number_input("Johans pensionsalder", min_value=55, max_value=75, value=67, step=1)
pensionsalder_m = st.sidebar.number_input("Markus' pensionsalder", min_value=55, max_value=75, value=65, step=1)

st.sidebar.divider()
st.sidebar.markdown("💡 *Aktiedepoter (ASK + Frie midler) og Markus' BSU er fastlåst og holdt ude af boligfinansieringen i disse beregninger.*")


# --- DYNAMISK SIMULERINGSFUNKTION ---
def calculate_drawdown_monthly_income(depot_total, current_age, target_age, net_return_rate):
    if current_age >= target_age:
        return 0
    years_left = target_age - current_age
    months_left = years_left * 12
    monthly_rate = net_return_rate / 12

    if monthly_rate == 0:
        return depot_total / months_left
    else:
        return depot_total * (monthly_rate * (1 + monthly_rate)**months_left) / ((1 + monthly_rate)**months_left - 1)

def get_emoji_status(barista_hours):
    if barista_hours == 0: return "🟢 0.0t"
    elif 0 < barista_hours <= 15: return f"🟡 {barista_hours:.1f}t"
    elif 15 < barista_hours <= 25: return f"🟠 {barista_hours:.1f}t"
    else: return f"🔴 {barista_hours:.1f}t"

def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, realkreditydelse_netto, ejerudgifter_og_fællesudgifter_total, bolig_solgt):
    return_rate_gross = global_return_rate_gross
    return_rate_net_drawdown = global_return_rate_net_drawdown
    inflation_rate = global_inflation_rate
    barista_wage_net_start = global_barista_wage_net
    
    pal_tax = 0.153
    weeks_per_month = 4.33
    age_j, age_m = 41, 32

    inkomst_j = st.session_state["inkomst_j"]
    inkomst_m = st.session_state["inkomst_m"]
    pension_j = st.session_state["pension_j"]
    pension_m = st.session_state["pension_m"]

    if bolig_solgt:
        cash_j = st.session_state["cash_j_base"]
        cash_m = st.session_state["cash_m_base"]
    else:
        cash_j, cash_m = 0, 0

    mangler_m = max(0, udbetaling_m - cash_m)
    faktisk_udbetaling_m = udbetaling_m - mangler_m
    udbetaling_j_total = udbetaling_j + mangler_m
    mangler_j = max(0, udbetaling_j_total - cash_j)
    faktisk_udbetaling_j = udbetaling_j_total - mangler_j

    overskud_cash_j = cash_j - faktisk_udbetaling_j
    overskud_cash_m = cash_m - faktisk_udbetaling_m

    depot_ask_j = st.session_state["basis_ask_j"]
    depot_free_j = st.session_state["basis_frie_j"] + overskud_cash_j
    depot_ask_m = st.session_state["basis_ask_m"]
    depot_free_m = st.session_state["basis_frie_m"] + overskud_cash_m

    fire_bortfald_j = ["A_kasse_Fagforening", "Loensikring"]
    fire_bortfald_m = ["A_kasse_Fagforening", "Loensikring", "Studielaan"]

    bolig_faelles = (realkreditydelse_netto + ejerudgifter_og_fællesudgifter_total) / 2
    
    start_inv_md_j = inkomst_j - (sum(st.session_state["budget_j"].values()) + bolig_faelles)
    start_inv_md_m = inkomst_m - (sum(st.session_state["budget_m"].values()) + bolig_faelles)
    
    start_fire_expenses_j = sum(v for k, v in st.session_state["budget_j"].items() if k not in fire_bortfald_j) + bolig_faelles
    start_fire_expenses_m = sum(v for k, v in st.session_state["budget_m"].items() if k not in fire_bortfald_m) + bolig_faelles

    if mangler_j > 0:
        st.error(f"⚠️ ADVARSEL: Udbetalingen er {f'{int(mangler_j):,}'.replace(',', '.')} kr. højere end jeres likviditet til boligkøb. Aktierne er fredet, så I skal øge lånet.")

    st.write("") 

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"JOHAN")
        st.markdown(f"""
        **Udbetaling (betalt af formue):** {f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.  
        **Realkreditydelse (egen andel):** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.  
        **Startdepot (Efter boligkøb):** {f'{int(depot_free_j + depot_ask_j):,}'.replace(',', '.')} kr.  
        **Mdl. opsparing:** {f'{int(start_inv_md_j):,}'.replace(',', '.')} kr.  
        **FIRE udgift (Start):** {f'{int(start_fire_expenses_j):,}'.replace(',', '.')} kr./md.
        """)
    
    with col2:
        st.subheader(f"MARKUS")
        st.markdown(f"""
        **Udbetaling (betalt af formue):** {f'{int(faktisk_udbetaling_m):,}'.replace(',', '.')} kr.  
        **Realkreditydelse (egen andel):** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.  
        **Startdepot (Efter boligkøb):** {f'{int(depot_free_m + depot_ask_m):,}'.replace(',', '.')} kr.  
        **Mdl. opsparing:** {f'{int(start_inv_md_m):,}'.replace(',', '.')} kr.  
        **FIRE udgift (Start):** {f'{int(start_fire_expenses_m):,}'.replace(',', '.')} kr./md.
        """)

    st.write("") 
    
    table_data = []
    j_full_fire_reached, m_full_fire_reached = False, False
    j_fire_age, m_fire_age = 0, 0
    pension_at_target_j, pension_at_target_m = 0, 0
    
    cur_fire_expenses_j = start_fire_expenses_j
    cur_fire_expenses_m = start_fire_expenses_m
    cur_yearly_savings_j = start_inv_md_j * 12
    cur_yearly_savings_m = start_inv_md_m * 12
    cur_barista_wage = barista_wage_net_start
    
    cur_progression_limit_j = 79400
    cur_progression_limit_m = 79400

    for year in range(0, 26):
        current_age_j = age_j + year
        current_age_m = age_m + year

        if year > 0:
            cur_fire_expenses_j *= (1 + inflation_rate)
            cur_fire_expenses_m *= (1 + inflation_rate)
            cur_yearly_savings_j *= (1 + inflation_rate)
            cur_yearly_savings_m *= (1 + inflation_rate)
            cur_barista_wage *= (1 + inflation_rate)
            cur_progression_limit_j *= (1 + inflation_rate)
            cur_progression_limit_m *= (1 + inflation_rate)

            if not j_full_fire_reached: depot_free_j += cur_yearly_savings_j
            if not m_full_fire_reached: depot_free_m += cur_yearly_savings_m

            ask_return_j = depot_ask_j * return_rate_gross
            depot_ask_j += ask_return_j - (ask_return_j * 0.17)
            free_return_j = depot_free_j * return_rate_gross
            free_tax_j = free_return_j * 0.27 if free_return_j <= cur_progression_limit_j else (cur_progression_limit_j * 0.27) + ((free_return_j - cur_progression_limit_j) * 0.42)
            depot_free_j += free_return_j - free_tax_j

            ask_return_m = depot_ask_m * return_rate_gross
            depot_ask_m += ask_return_m - (ask_return_m * 0.17)
            free_return_m = depot_free_m * return_rate_gross
            free_tax_m = free_return_m * 0.27 if free_return_m <= cur_progression_limit_m else (cur_progression_limit_m * 0.27) + ((free_return_m - cur_progression_limit_m) * 0.42)
            depot_free_m += free_return_m - free_tax_m

        total_depot_j_val = depot_ask_j + depot_free_j
        passive_j = calculate_drawdown_monthly_income(total_depot_j_val, current_age_j, pensionsalder_j, return_rate_net_drawdown)
        shortfall_j = max(0, cur_fire_expenses_j - passive_j)
        hours_j = shortfall_j / (cur_barista_wage * weeks_per_month)

        total_depot_m_val = depot_ask_m + depot_free_m
        passive_m = calculate_drawdown_monthly_income(total_depot_m_val, current_age_m, pensionsalder_m, return_rate_net_drawdown)
        shortfall_m = max(0, cur_fire_expenses_m - passive_m)
        hours_m = shortfall_m / (cur_barista_wage * weeks_per_month)

        table_data.append({
            "År": year,
            "J.alder": current_age_j,
            "J.depot (M)": f"{total_depot_j_val / 1_000_000:.2f}".replace('.', ','),
            "J.Passiv (kr)": f"{int(passive_j):,}".replace(',', '.'),
            "J.Arbtid": get_emoji_status(hours_j),
            "M.alder": current_age_m,
            "M.depot (M)": f"{total_depot_m_val / 1_000_000:.2f}".replace('.', ','),
            "M.Passiv (kr)": f"{int(passive_m):,}".replace(',', '.'),
            "M.Arbtid": get_emoji_status(hours_m)
        })

        if hours_j <= 0 and not j_full_fire_reached:
            j_full_fire_reached = True
            j_fire_age = current_age_j
            pension_at_target_j = pension_j * ((1 + (return_rate_gross * (1 - pal_tax))) ** (pensionsalder_j - age_j))

        if hours_m <= 0 and not m_full_fire_reached:
            m_full_fire_reached = True
            m_fire_age = current_age_m
            pension_at_target_m = pension_m * ((1 + (return_rate_gross * (1 - pal_tax))) ** (pensionsalder_m - age_m))

        if hours_j <= 0 and hours_m <= 0:
            break

    df = pd.DataFrame(table_data)
    st.table(df.set_index("År"))
    
    st.write("") 

    if j_full_fire_reached:
        st.markdown(f"""
        <div class='success-box'>
            ✅ <b>Johans brofinansiering er sikret ved alder {j_fire_age}.</b><br>
            Pension forventes ca. {pension_at_target_j / 1_000_000:.2f}M kr.
        </div>
        """, unsafe_allow_html=True)
        
    if m_full_fire_reached:
        st.markdown(f"""
        <div class='success-box'>
            ✅ <b>Markus brofinansiering er sikret ved alder {m_fire_age}.</b><br>
            Pension forventes ca. {pension_at_target_m / 1_000_000:.2f}M kr.
        </div>
        """, unsafe_allow_html=True)


# --- HOVEDNAVIGATION (PILLS) ---
view_selection = st.pills(
    "Navigation", 
    options=["Boligscenarier", "⚙️ Basisdata & Opsætning"], 
    default="Boligscenarier", 
    label_visibility="collapsed"
)
st.write("")

# --- VISNING 1: OPSÆTNING ---
if view_selection == "⚙️ Basisdata & Opsætning":
    st.subheader("Konfiguration af personlig økonomi")
    st.markdown("Ændringer foretaget her gemmes automatisk og bruges i alle boligscenarier.")
    
    col_setup_j, col_setup_m = st.columns(2)
    
    with col_setup_j:
        st.markdown("### 👤 JOHAN DATA")
        st.session_state["inkomst_j"] = st.number_input("Månedsløn (Netto kr.)", min_value=0, value=st.session_state["inkomst_j"], step=500, key="input_ink_j")
        st.session_state["pension_j"] = st.number_input("Pensionsopsparing (kr.)", min_value=0, value=st.session_state["pension_j"], step=10000, key="input_pen_j")
        
        st.markdown("**Formue før boligkøb:**")
        st.session_state["cash_j_base"] = st.number_input("Kontanter / Friværdi (kr.)", min_value=0, value=st.session_state["cash_j_base"], step=10000, key="input_cash_j")
        st.session_state["basis_ask_j"] = st.number_input("Aktiesparekonto (kr.)", min_value=0, value=st.session_state["basis_ask_j"], step=5000, key="input_ask_j")
        st.session_state["basis_frie_j"] = st.number_input("Frie midler / Aktier (kr.)", min_value=0, value=st.session_state["basis_frie_j"], step=5000, key="input_frie_j")
        
        st.markdown("**Personligt Budget (Faste udgifter):**")
        df_budget_j = pd.DataFrame(list(st.session_state["budget_j"].items()), columns=["Kategori", "Beløb (kr./md)"])
        edited_df_j = st.data_editor(df_budget_j, hide_index=True, use_container_width=True, key="editor_budget_j")
        st.session_state["budget_j"] = dict(edited_df_j.values)

    with col_setup_m:
        st.markdown("### 👤 MARKUS DATA")
        st.session_state["inkomst_m"] = st.number_input("Månedsløn (Netto kr.)", min_value=0, value=st.session_state["inkomst_m"], step=500, key="input_ink_m")
        st.session_state["pension_m"] = st.number_input("Pensionsopsparing (kr.)", min_value=0, value=st.session_state["pension_m"], step=10000, key="input_pen_m")
        
        st.markdown("**Formue før boligkøb:**")
        st.session_state["cash_m_base"] = st.number_input("Kontanter / Friværdi (kr.)", min_value=0, value=st.session_state["cash_m_base"], step=10000, key="input_cash_m")
        st.session_state["basis_ask_m"] = st.number_input("Aktiesparekonto (kr.)", min_value=0, value=st.session_state["basis_ask_m"], step=5000, key="input_ask_m")
        st.session_state["basis_frie_m"] = st.number_input("Frie midler / Aktier (kr.)", min_value=0, value=st.session_state["basis_frie_m"], step=5000, key="input_frie_m")
        
        st.markdown("**Personligt Budget (Faste udgifter):**")
        df_budget_m = pd.DataFrame(list(st.session_state["budget_m"].items()), columns=["Kategori", "Beløb (kr./md)"])
        edited_df_m = st.data_editor(df_budget_m, hide_index=True, use_container_width=True, key="editor_budget_m")
        st.session_state["budget_m"] = dict(edited_df_m.values)


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
