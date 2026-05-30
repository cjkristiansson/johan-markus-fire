import streamlit as st
import pandas as pd

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

# Formue før boligkøb
if "cash_j_base" not in st.session_state: st.session_state["cash_j_base"] = 2567500
if "cash_m_base" not in st.session_state: st.session_state["cash_m_base"] = 1153888
if "basis_ask_j" not in st.session_state: st.session_state["basis_ask_j"] = 174000
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 65000
if "basis_ask_m" not in st.session_state: st.session_state["basis_ask_m"] = 170000
if "basis_frie_m" not in st.session_state: st.session_state["basis_frie_m"] = 0

# Toggles (Sikrer default-værdier er sat til False)
if "use_bsu_m" not in st.session_state: st.session_state["use_bsu_m"] = False
if "use_loensikring_j" not in st.session_state: st.session_state["use_loensikring_j"] = False
if "use_loensikring_m" not in st.session_state: st.session_state["use_loensikring_m"] = False

# Personlige budgetter
if "budget_j" not in st.session_state:
    st.session_state["budget_j"] = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 0, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
if "budget_m" not in st.session_state:
    st.session_state["budget_m"] = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 0, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

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
    * **Omlægningsscenarie:** Kan aktiveres under tabellerne. Modulet er deaktiveret som standard. Når det slås til, udregnes restgælden dynamisk (fratrukket jeres løbende afdrag op til omlægningsåret), hvorefter ny rente, afdrag og omkostninger lægges på det nye lån.
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
    
    aktiver_oml = st.session_state.get(f"aktiver_oml_{ydelse_key}", False)
    oml_aar = st.session_state.get(f"oml_aar_{ydelse_key}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{ydelse_key}", 4.0) / 100
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{ydelse_key}", False)
    oml_omk = st.session_state.get(f"oml_omk_{ydelse_key}", 50000)

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

    with st.expander("🏠 Vis økonomiske detaljer & lån", expanded=False):
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        with col_inp:
            st.markdown(
                f"<p style='margin-bottom: 60px; margin-top: 0; line-height: 1.3;'>"
                f"{int(cash_pct)}% kontantudbetaling ({f'{int(total_udbetaling):,}'.replace(',', '.')} kr.) | {int(loan_pct)}% lån</p>", 
                unsafe_allow_html=True
            )
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key)

        depot_free_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        depot_free_m = st.session_state["basis_frie_m"] + (cash_m - faktisk_udbetaling_m)
        depot_ask_j, depot_ask_m = st.session_state["basis_ask_j"], st.session_state["basis_ask_m"]

        bolig_faelles = (realkreditydelse_netto + ejerudgifter_total + boligskat_md) / 2
        
        # Budgetterne indeholder allerede den korrekte lønsikring ud fra brugerens toggle
        budget_j_total = sum(st.session_state["budget_j"].values())
        budget_m_total = sum(st.session_state["budget_m"].values())

        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_faelles)
        start_inv_md_m = st.session_state["inkomst_m"] - (budget_m_total + bolig_faelles) + bsu_passive
        
        # I FIRE fasen fjernes A-kasse og Lønsikring altid uanset hvad
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

    restgaeld_start = boligpris - total_udbetaling
    bolig_faelles_current = bolig_faelles
    
    if "Valby" in scenario_name:
        oprindelig_rente_mnd = 0.024 / 12
        start_afdrag_mnd = 6929
    else:
        oprindelig_rente_mnd = 0.04 / 12

    table_data = []
    j_reached, m_reached = False, False
    j_fire_age, m_fire_age = 0, 0
    
    for year in range(0, 26):
        c_age_j, c_age_m = age_j + year, age_m + year
        
        # Omlægning
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > 0:
            mdr_gaaet = oml_aar * 12
            if "Valby" in scenario_name:
                afdraget_beloeb = start_afdrag_mnd * (((1 + oprindelig_rente_mnd)**mdr_gaaet - 1) / oprindelig_rente_mnd)
                restgaeld_ved_oml = max(0, restgaeld_start - afdraget_beloeb)
            else:
                restgaeld_ved_oml = restgaeld_start * ((1 + oprindelig_rente_mnd)**360 - (1 + oprindelig_rente_mnd)**mdr_gaaet) / ((1 + oprindelig_rente_mnd)**360 - 1)
            
            ny_hovedstol = restgaeld_ved_oml + oml_omk
            mnd_rente_ny = oml_rente / 12
            
            if not oml_afdrag_fri:
                ny_ydelse = ny_hovedstol * (mnd_rente_ny * (1 + mnd_rente_ny)**360) / ((1 + mnd_rente_ny)**360 - 1)
            else:
                ny_ydelse = ny_hovedstol * mnd_rente_ny
                
            renter_md = (ny_hovedstol * oml_rente) / 12
            netto_bolig_faelles = (ny_ydelse + ejerudgifter_total + boligskat_md - (renter_md * 0.256)) / 2
            
            diff_faelles = bolig_faelles_current - netto_bolig_faelles
            start_fire_j -= diff_faelles; start_fire_m -= diff_faelles
            start_inv_md_j += diff_faelles; start_inv_md_m += diff_faelles
            bolig_faelles_current = netto_bolig_faelles

        # Beskatning, Vækst & Opsparing
        if year > 0:
            start_fire_j *= (1 + global_inflation_rate); start_fire_m *= (1 + global_inflation_rate)
            
            # --- PROGRESSIV LAGERBESKATNING (Regel-compliance) ---
            # Grænsen fremskrives med inflation
            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            prog_limit_m = 79400 * ((1 + global_inflation_rate)**year)
            
            # Afkast
            return_frie_j = depot_free_j * global_return_rate_gross
            return_frie_m = depot_free_m * global_return_rate_gross
            
            # Skatteberegning (27% under, 42% over)
            tax_j = (return_frie_j * 0.27) if return_frie_j <= prog_limit_j else (prog_limit_j * 0.27 + (return_frie_j - prog_limit_j) * 0.42)
            tax_m = (return_frie_m * 0.27) if return_frie_m <= prog_limit_m else (prog_limit_m * 0.27 + (return_frie_m - prog_limit_m) * 0.42)
            
            # Tilføj afkast minus skat
            depot_free_j += (return_frie_j - tax_j)
            depot_free_m += (return_frie_m - tax_m)
            
            # ASK (17% flad skat)
            depot_ask_j *= (1 + global_return_rate_gross * 0.83)
            depot_ask_m *= (1 + global_return_rate_gross * 0.83)
            
            # Indskud af årets nye opsparing (ved slutningen af året)
            if not j_reached: depot_free_j += start_inv_md_j * 12 * ((1 + global_inflation_rate)**year)
            if not m_reached: depot_free_m += start_inv_md_m * 12 * ((1 + global_inflation_rate)**year)

        p_j = calculate_drawdown_monthly_income(depot_ask_j + depot_free_j, c_age_j, pensionsalder_j, global_return_rate_net_drawdown)
        p_m_drawdown = calculate_drawdown_monthly_income(depot_ask_m + depot_free_m, c_age_m, pensionsalder_m, global_return_rate_net_drawdown)
        p_m_total = p_m_drawdown + bsu_passive

        h_j = max(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)
        h_m = max(0, start_fire_m - p_m_total) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        table_data.append({"År": year, "J.alder": c_age_j, "J.depot (M)": f"{(depot_ask_j + depot_free_j)/1e6:.2f}", "J.Passiv (kr)": f"{int(p_j):,}".replace(',', '.'), "J.Arbtid": get_emoji_status(h_j), "M.alder": c_age_m, "M.depot (M)": f"{(depot_ask_m + depot_free_m)/1e6:.2f}", "M.Passiv (kr)": f"{int(p_m_total):,}".replace(',', '.'), "M.Arbtid": get_emoji_status(h_m)})
        
        if h_j <= 0 and not j_reached: j_reached = True; j_fire_age = c_age_j
        if h_m <= 0 and not m_reached: m_reached = True; m_fire_age = c_age_m
        if h_j <= 0 and h_m <= 0: break

    st.table(pd.DataFrame(table_data).set_index("År"))

    with st.expander("🔄 Omlægningsscenarie", expanded=False):
        st.toggle("Aktiver omlægningsscenarie", value=False, key=f"aktiver_oml_{ydelse_key}")
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        col_o1.number_input("År for omlægning (0-10)", min_value=0, max_value=10, value=5, key=f"oml_aar_{ydelse_key}")
        col_o2.number_input("Ny rente + bidrag (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1, key=f"oml_rente_{ydelse_key}")
        col_o3.toggle("Afdragsfrihed aktiveret", value=False, key=f"oml_afdrag_fri_{ydelse_key}")
        col_o4.number_input("Omkostninger (kr)", value=50000, step=5000, key=f"oml_omk_{ydelse_key}")


def simulate_solo_fire_plan(scenario_name, boligpris, udbetaling_j, ydelse_default, ydelse_key, ejerudgifter_total, boligskat_md):
    pal_tax, weeks_per_month, age_j = 0.153, 4.33, 41
    
    s_key = f"solo_{ydelse_key}"
    aktiver_oml = st.session_state.get(f"aktiver_oml_{s_key}", False)
    oml_aar = st.session_state.get(f"oml_aar_{s_key}", 5)
    oml_rente = st.session_state.get(f"oml_rente_{s_key}", 4.0) / 100
    oml_afdrag_fri = st.session_state.get(f"oml_afdrag_fri_{s_key}", False)
    oml_omk = st.session_state.get(f"oml_omk_{s_key}", 50000)

    cash_j = st.session_state["cash_j_base"]
    faktisk_udbetaling_j = min(udbetaling_j, cash_j)
    cash_pct = (faktisk_udbetaling_j / boligpris * 100) if boligpris > 0 else 0
    loan_pct = 100 - cash_pct

    with st.expander("⚙️ Vis økonomiske detaljer & lån", expanded=False):
        col_j, col_m, col_inp = st.columns([0.41, 0.41, 0.18], vertical_alignment="bottom")

        with col_inp:
            st.markdown(
                f"<p style='margin-bottom: 105px; margin-top: 0; line-height: 1.3;'>"
                f"{int(cash_pct)}% kontantudbetaling ({f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.) | {int(loan_pct)}% lån</p>", 
                unsafe_allow_html=True
            )
            realkreditydelse_netto = st.number_input("Realkreditydelse", value=ydelse_default, step=100, key=ydelse_key)
        
        depot_free_j = st.session_state["basis_frie_j"] + (cash_j - faktisk_udbetaling_j)
        depot_ask_j = st.session_state["basis_ask_j"]

        solo_budget_j = st.session_state["budget_j"].copy()
        solo_budget_j["Mad"] = 3000

        bolig_total = realkreditydelse_netto + ejerudgifter_total + boligskat_md
        budget_j_total = sum(solo_budget_j.values())
        
        start_inv_md_j = st.session_state["inkomst_j"] - (budget_j_total + bolig_total)
        start_fire_j = sum(v for k, v in solo_budget_j.items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_total

        with col_j:
            st.subheader(f"JOHAN (SOLO)")
            st.markdown(f"""
            **Boligpris:** {f'{int(boligpris):,}'.replace(',', '.')} kr.  
            **Udbetaling:** {f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.  
            **Boligudgifter total:** {f'{int(bolig_total):,}'.replace(',', '.')} kr./md.  
            **Startdepot:** {f'{int(depot_free_j + depot_ask_j):,}'.replace(',', '.')} kr.  
            **Mdl. opsparing:** {f'{int(start_inv_md_j):,}'.replace(',', '.')} kr.  
            **Mdl. Udgifter:** {f'{int(start_fire_j):,}'.replace(',', '.')} kr./md.
            """)
            
    st.write("")

    restgaeld_start = boligpris - faktisk_udbetaling_j
    bolig_total_current = bolig_total
    oprindelig_rente_mnd = 0.04 / 12

    table_data = []
    j_reached = False; j_fire_age = 0
    
    for year in range(0, 26):
        c_age_j = age_j + year
        
        if aktiver_oml and year == oml_aar and boligpris > 0 and oml_aar > 0:
            mdr_gaaet = oml_aar * 12
            restgaeld_ved_oml = restgaeld_start * ((1 + oprindelig_rente_mnd)**360 - (1 + oprindelig_rente_mnd)**mdr_gaaet) / ((1 + oprindelig_rente_mnd)**360 - 1)
            ny_hovedstol = restgaeld_ved_oml + oml_omk
            mnd_rente_ny = oml_rente / 12
            
            if not oml_afdrag_fri: ny_ydelse = ny_hovedstol * (mnd_rente_ny * (1 + mnd_rente_ny)**360) / ((1 + mnd_rente_ny)**360 - 1)
            else: ny_ydelse = ny_hovedstol * mnd_rente_ny
                
            renter_md = (ny_hovedstol * oml_rente) / 12
            netto_bolig_total = ny_ydelse + ejerudgifter_total + boligskat_md - (renter_md * 0.256)
            diff_bolig = bolig_total_current - netto_bolig_total
            start_fire_j -= diff_bolig; start_inv_md_j += diff_bolig
            bolig_total_current = netto_bolig_total

        if year > 0:
            start_fire_j *= (1 + global_inflation_rate)
            prog_limit_j = 79400 * ((1 + global_inflation_rate)**year)
            return_frie_j = depot_free_j * global_return_rate_gross
            tax_j = (return_frie_j * 0.27) if return_frie_j <= prog_limit_j else (prog_limit_j * 0.27 + (return_frie_j - prog_limit_j) * 0.42)
            
            depot_free_j += (return_frie_j - tax_j)
            depot_ask_j *= (1 + global_return_rate_gross * 0.83)
            if not j_reached: depot_free_j += start_inv_md_j * 12 * ((1 + global_inflation_rate)**year)

        p_j = calculate_drawdown_monthly_income(depot_ask_j + depot_free_j, c_age_j, pensionsalder_j, global_return_rate_net_drawdown)
        h_j = max(0, start_fire_j - p_j) / (global_barista_wage_net * ((1+global_inflation_rate)**year) * weeks_per_month)

        table_data.append({"År": year, "Alder": c_age_j, "Depot (M)": f"{(depot_ask_j + depot_free_j)/1e6:.2f}", "Passiv Indkomst (kr)": f"{int(p_j):,}".replace(',', '.'), "Arbejdstid (Barista)": get_emoji_status(h_j)})
        
        if h_j <= 0 and not j_reached: j_reached = True; j_fire_age = c_age_j

    st.table(pd.DataFrame(table_data).set_index("År"))
    
    with st.expander("🔄 Omlægningsscenarie", expanded=False):
        st.toggle("Aktiver omlægningsscenarie", value=False, key=f"aktiver_oml_{s_key}")
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        col_o1.number_input("År for omlægning (0-10)", min_value=0, max_value=10, value=5, key=f"oml_aar_{s_key}")
        col_o2.number_input("Ny rente + bidrag (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1, key=f"oml_rente_{s_key}")
        col_o3.toggle("Afdragsfrihed aktiveret", value=False, key=f"oml_afdrag_fri_{s_key}")
        col_o4.number_input("Omkostninger (kr)", value=50000, step=5000, key=f"oml_omk_{s_key}")


# --- VISNING 1: OPSÆTNING ---
if view_selection == "⚙️ Basisdata & Opsætning":
    st.subheader("Konfiguration af personlig økonomi")
    col_setup_j, col_setup_m = st.columns(2)
    
    with col_setup_j:
        st.markdown("### 👤 JOHAN DATA")
        st.session_state["inkomst_j"] = st.number_input("Månedsløn (Netto kr.)", value=st.session_state["inkomst_j"], step=500, key="inp_j")
        st.session_state["pension_j"] = st.number_input("Pensionsopsparing (kr.)", min_value=0, value=st.session_state["pension_j"], step=10000, key="input_pen_j")
        st.session_state["cash_j_base"] = st.number_input("Kontanter / Friværdi (kr.)", value=st.session_state["cash_j_base"], step=10000, key="csh_j")
        st.session_state["basis_ask_j"] = st.number_input("Aktiesparekonto (kr.)", value=st.session_state["basis_ask_j"], key="ask_j")
        st.session_state["basis_frie_j"] = st.number_input("Frie midler / Aktier (kr.)", value=st.session_state["basis_frie_j"], key="fr_j")
        
        # Toggle og dynamisk ordbog-opdatering for Johan
        st.session_state["use_loensikring_j"] = st.toggle("Inddrag Lønsikring (1.836 kr.)", value=st.session_state.get("use_loensikring_j", False), key="toggle_loen_j")
        st.session_state["budget_j"]["Loensikring"] = 1836 if st.session_state["use_loensikring_j"] else 0
        
        df_j = st.data_editor(pd.DataFrame(list(st.session_state["budget_j"].items()), columns=["Kategori", "Beløb"]), hide_index=True, use_container_width=True, key="ed_j")
        st.session_state["budget_j"] = dict(df_j.values)
        st.write("")
        
    with col_setup_m:
        st.markdown("### 👤 MARKUS DATA")
        st.session_state["inkomst_m"] = st.number_input("Månedsløn (Netto kr.)", value=st.session_state["inkomst_m"], step=500, key="inp_m")
        st.session_state["pension_m"] = st.number_input("Pensionsopsparing (kr.)", min_value=0, value=st.session_state["pension_m"], step=10000, key="input_pen_m")
        st.session_state["cash_m_base"] = st.number_input("Kontanter / Friværdi (kr.)", value=st.session_state["cash_m_base"], step=10000, key="csh_m")
        st.session_state["basis_ask_m"] = st.number_input("Aktiesparekonto (kr.)", value=st.session_state["basis_ask_m"], key="ask_m")
        st.session_state["basis_frie_m"] = st.number_input("Frie midler / Aktier (kr.)", value=st.session_state["basis_frie_m"], key="fr_m")
        
        # Toggle og dynamisk ordbog-opdatering for Markus
        st.session_state["use_loensikring_m"] = st.toggle("Inddrag Lønsikring (720 kr.)", value=st.session_state.get("use_loensikring_m", False), key="toggle_loen_m")
        st.session_state["budget_m"]["Loensikring"] = 720 if st.session_state["use_loensikring_m"] else 0
        
        df_m = st.data_editor(pd.DataFrame(list(st.session_state["budget_m"].items()), columns=["Kategori", "Beløb"]), hide_index=True, use_container_width=True, key="ed_m")
        st.session_state["budget_m"] = dict(df_m.values)
        st.write("")
        st.session_state["use_bsu_m"] = st.toggle("Inddrag Norsk BSU", value=st.session_state.get("use_bsu_m", False), key="toggle_bsu_m")

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
