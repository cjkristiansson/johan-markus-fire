import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

# --- GLOBAL CSS ---
st.markdown("""
<style>
    .success-box {
        background-color: #e6f4ea;
        border-left: 5px solid #1e8e3e;
        padding: 16px 20px;
        border-radius: 8px;
        color: #0d652d;
        font-family: sans-serif;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    @media (prefers-color-scheme: dark) {
        .success-box {
            background-color: #13271a;
            border-left: 5px solid #81c995;
            color: #a8dab5;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("FIRE Brofinansiering: Johan & Markus")

# --- 1. SIDEBAR TIL INTERAKTIVE VARIABLER ---
st.sidebar.header("🌍 Globale Antagelser")
st.sidebar.markdown("Juster variablerne for at stress-teste alle scenarier samtidigt.")

global_return_rate_gross = st.sidebar.slider("Bruttoafkast under opsparing (%)", min_value=3.0, max_value=10.0, value=7.0, step=0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast i passiv fase (%)", min_value=2.0, max_value=8.0, value=4.5, step=0.1) / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", min_value=0.0, max_value=5.0, value=2.0, step=0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5)

st.sidebar.divider()
st.sidebar.markdown("💡 *Aktiedepoter (ASK + Frie midler) og Markus' BSU er fastlåst og holdt ude af boligfinansieringen i disse beregninger.*")

# --- BASIS DATA (Brugt i global visning) ---
inkomst_j, inkomst_m = 38468, 32983
pension_j, pension_m = 845000, 570000
cash_j_base, cash_m_base = 2408888, 983888
basis_ask_j, basis_frie_j = 174000, 71000
basis_ask_m, basis_frie_m = 170000, 0
pensionsalder_j, pensionsalder_m = 67, 67

budget_j = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1674, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
budget_m = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 720, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

def format_budget(b):
    return "\n".join([f"- {k.replace('_', ' ')}: {f'{v:,}'.replace(',', '.')} kr." for k, v in b.items() if v > 0])

# --- GLOBALE ACCORDIONS ---
with st.expander("⚙️ Modellens Regler & Logik"):
    st.markdown("""
    * **Trin 0 (Boligkøb først):** Startdepotet i år 1 er formuen *efter* udbetaling til bolig. Aktiedepoter er låst til FIRE.
    * **Lagerbeskatning:** ASK beskattes fladt med 17%. Frie midler beskattes progressivt (27% op til grænsen, 42% derover). Progressionsgrænsen (61.300 kr.) indekseres årligt med inflationen.
    * **Inflationseffekt:** Udgifter, opsparingsrate og progressionsgrænser stiger alle med den valgte inflationsrate år for år i modellen.
    * **Pension adskilt:** Pensionsdepoter bruges *ikke* før 67 år. Indbetalinger stopper det år fuld FIRE nås, hvorefter depotet kun vokser med afkast minus PAL-skat (15,3%).
    * **Barista-timer:** Timer beregnes på *restbehovet*. Passiv indkomst fra depotet fratrækkes FIRE-udgifterne først.
    * **Dynamiske boligudgifter:** Bliver der optaget realkreditlån, indgår ydelsen fuldt ud i de månedlige FIRE-udgifter for det givne scenarie.
    """)

with st.expander("📊 Se Grunddata (Formue før bolig, Budget & Pension)"):
    col_j, col_m = st.columns(2)
    with col_j:
        st.markdown(f"""
        ### JOHAN
        **Løn (Netto):** {f"{inkomst_j:,}".replace(',', '.')} kr./md  
        **Pension:** {f"{pension_j:,}".replace(',', '.')} kr. (Udbetales fra {pensionsalder_j} år)  
        **Formue før boligkøb:**
        - Kontanter: {f"{cash_j_base:,}".replace(',', '.')} kr.
        - ASK: {f"{basis_ask_j:,}".replace(',', '.')} kr.
        - Frie midler: {f"{basis_frie_j:,}".replace(',', '.')} kr.
        
        **Personligt Budget (Faste):**
        {format_budget(budget_j)}
        """)
    with col_m:
        st.markdown(f"""
        ### MARKUS
        **Løn (Netto):** {f"{inkomst_m:,}".replace(',', '.')} kr./md  
        **Pension:** {f"{pension_m:,}".replace(',', '.')} kr. (Udbetales fra {pensionsalder_m} år)  
        **Formue før boligkøb:**
        - Kontanter: {f"{cash_m_base:,}".replace(',', '.')} kr.
        - ASK: {f"{basis_ask_m:,}".replace(',', '.')} kr.
        - Frie midler: {f"{basis_frie_m:,}".replace(',', '.')} kr.
        
        **Personligt Budget (Faste):**
        {format_budget(budget_m)}
        """)

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

    if bolig_solgt:
        cash_j, cash_m = cash_j_base, cash_m_base
    else:
        cash_j, cash_m = 0, 0

    mangler_m = max(0, udbetaling_m - cash_m)
    faktisk_udbetaling_m = udbetaling_m - mangler_m
    udbetaling_j_total = udbetaling_j + mangler_m
    mangler_j = max(0, udbetaling_j_total - cash_j)
    faktisk_udbetaling_j = udbetaling_j_total - mangler_j

    overskud_cash_j = cash_j - faktisk_udbetaling_j
    overskud_cash_m = cash_m - faktisk_udbetaling_m

    depot_ask_j = basis_ask_j
    depot_free_j = basis_frie_j + overskud_cash_j
    depot_ask_m = basis_ask_m
    depot_free_m = basis_frie_m + overskud_cash_m

    fire_bortfald_j = ["A_kasse_Fagforening", "Loensikring"]
    fire_bortfald_m = ["A_kasse_Fagforening", "Loensikring", "Studielaan"]

    bolig_faelles = (realkreditydelse_netto + ejerudgifter_og_fællesudgifter_total) / 2
    
    start_inv_md_j = inkomst_j - (sum(budget_j.values()) + bolig_faelles)
    start_inv_md_m = inkomst_m - (sum(budget_m.values()) + bolig_faelles)
    
    start_fire_expenses_j = sum(v for k, v in budget_j.items() if k not in fire_bortfald_j) + bolig_faelles
    start_fire_expenses_m = sum(v for k, v in budget_m.items() if k not in fire_bortfald_m) + bolig_faelles

    if mangler_j > 0:
        st.error(f"⚠️ ADVARSEL: Udbetalingen er {f'{int(mangler_j):,}'.replace(',', '.')} kr. højere end jeres likviditet til boligkøb. Aktierne er fredet, så I skal øge lånet.")

    st.write("") # Whitespace

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"JOHAN")
        st.write(f"**Udbetaling (betalt af formue):** {f'{int(faktisk_udbetaling_j):,}'.replace(',', '.')} kr.")
        st.write(f"**Realkreditydelse (egen andel):** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.")
        st.write(f"**Startdepot (Efter boligkøb):** {f'{int(depot_free_j + depot_ask_j):,}'.replace(',', '.')} kr.")
        st.write(f"**Mdl. opsparing:** {f'{int(start_inv_md_j):,}'.replace(',', '.')} kr.")
        st.write(f"**FIRE udgift (Start):** {f'{int(start_fire_expenses_j):,}'.replace(',', '.')} kr./md.")
    
    with col2:
        st.subheader(f"MARKUS")
        st.write(f"**Udbetaling (betalt af formue):** {f'{int(faktisk_udbetaling_m):,}'.replace(',', '.')} kr.")
        st.write(f"**Realkreditydelse (egen andel):** {f'{int(realkreditydelse_netto / 2):,}'.replace(',', '.')} kr./md.")
        st.write(f"**Startdepot (Efter boligkøb):** {f'{int(depot_free_m + depot_ask_m):,}'.replace(',', '.')} kr.")
        st.write(f"**Mdl. opsparing:** {f'{int(start_inv_md_m):,}'.replace(',', '.')} kr.")
        st.write(f"**FIRE udgift (Start):** {f'{int(start_fire_expenses_m):,}'.replace(',', '.')} kr./md.")

    st.write("") # Whitespace
    
    table_data = []
    j_full_fire_reached, m_full_fire_reached = False, False
    j_fire_age, m_fire_age = 0, 0
    pension_at_target_j, pension_at_target_m = 0, 0
    
    cur_fire_expenses_j = start_fire_expenses_j
    cur_fire_expenses_m = start_fire_expenses_m
    cur_yearly_savings_j = start_inv_md_j * 12
    cur_yearly_savings_m = start_inv_md_m * 12
    cur_barista_wage = barista_wage_net_start
    cur_progression_limit_j = 61300
    cur_progression_limit_m = 61300

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

    # Fjern index på Dataframen for et renere look
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    
    st.write("") # Whitespace

    # Custom styling til FIRE beskeder i stedet for default st.success
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

# --- KØRSELS-SEKTION MED TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["Plan A (4.0M)", "Plan B (4.5M)", "Plan C (5.0M)", "Plan D (Valby)"])

with tab1:
    simulate_joint_fire_plan("Plan A (4.0M Bolig)", 4000000, 1846222, 1153888, 4075, 4564, bolig_solgt=True)
with tab2:
    simulate_joint_fire_plan("Plan B (4.5M Bolig)", 4500000, 2250000, 1125000, 4576, 4564, bolig_solgt=True)
with tab3:
    simulate_joint_fire_plan("Plan C (5.0M Bolig)", 5000000, 2408888, 983888, 6519, 4564, bolig_solgt=True)
with tab4:
    simulate_joint_fire_plan("Plan D (Valby Nuværende)", 6700000, 0, 0, 15230, 4564, bolig_solgt=False)
