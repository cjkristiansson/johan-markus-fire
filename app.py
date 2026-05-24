import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

st.title("FIRE Brofinansiering: Johan & Markus")

with st.expander("⚙️ Modellens Regler & Logik"):
    st.markdown("""
    * **Trin 0 (Boligkøb først):** Startdepotet i år 1 er formuen *efter* udbetaling til bolig. Aktiedepoter og BSU-konto er låst til FIRE og bruges ikke som udbetaling.
    * **Lagerbeskatning:** Afkast af Aktiesparekonto (ASK) beskattes fladt med 17%. Frie midler beskattes progressivt (27% op til grænsen, 42% derover). Progressionsgrænsen (start 79.400 kr.) indekseres med 2% årligt.
    * **Pension adskilt fra FIRE:** Pensionsdepoter (PFA, Velliv etc.) bruges *ikke* til at finansiere perioden før 67 år. De dækker udelukkende tiden fra pensionsalderen.
    * **Ingen indbetaling efter FIRE:** Pensionsindbetalinger stopper det år, fuld FIRE nås. Depotet vokser derefter kun med afkast minus PAL-skat (15,3%).
    * **Barista-timer:** Timer beregnes på *restbehovet*. Passiv indkomst fra depotet fratrækkes FIRE-udgifterne først. Det resterende dækkes via nettoløn (135 kr./t).
    * **Dynamiske boligudgifter:** FIRE-udgifterne afspejler det valgte scenarie. Bliver der optaget realkreditlån, indgår ydelsen fuldt ud i de månedlige FIRE-udgifter.
    """)

def calculate_drawdown_monthly_income(depot_total, current_age, target_age, net_return_rate=0.045):
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
    if barista_hours == 0:
        return "🟢 0.0t"
    elif 0 < barista_hours <= 15:
        return f"🟡 {barista_hours:.1f}t"
    elif 15 < barista_hours <= 25:
        return f"🟠 {barista_hours:.1f}t"
    else:
        return f"🔴 {barista_hours:.1f}t"

def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, realkreditydelse_netto, ejerudgifter_og_fællesudgifter_total, max_years=25, bolig_solgt=True):
    return_rate_gross = 0.07
    return_rate_net_drawdown = 0.045 
    inflation_rate = 0.02
    progression_limit_j = 79400
    progression_limit_m = 79400
    pal_tax = 0.153
    barista_wage_net = 135 
    weeks_per_month = 4.33

    age_j, basis_ask_j, basis_frie_j, pension_j, pensionsudbetalingsalder_j = 41, 174000, 71000, 845000, 67
    age_m, basis_ask_m, basis_frie_m, pension_m, pensionsudbetalingsalder_m = 32, 170000, 0, 570000, 67
    inkomst_j = 38468
    inkomst_m = 32000 + 983

    if bolig_solgt:
        cash_j, cash_m = 2408888, 983888
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

    budget_j = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1674, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
    budget_m = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 720, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
    fire_bortfald_j = ["A_kasse_Fagforening", "Loensikring"]
    fire_bortfald_m = ["A_kasse_Fagforening", "Loensikring", "Studielaan"]

    bolig_faelles = (realkreditydelse_netto + ejerudgifter_og_fællesudgifter_total) / 2
    
    inv_md_j = inkomst_j - (sum(budget_j.values()) + bolig_faelles)
    inv_md_m = inkomst_m - (sum(budget_m.values()) + bolig_faelles)
    yearly_savings_j = inv_md_j * 12
    yearly_savings_m = inv_md_m * 12

    fire_expenses_j = sum(v for k, v in budget_j.items() if k not in fire_bortfald_j) + bolig_faelles
    fire_expenses_m = sum(v for k, v in budget_m.items() if k not in fire_bortfald_m) + bolig_faelles

    if mangler_j > 0:
        st.error(f"⚠️ ADVARSEL: Udbetalingen er {int(mangler_j):,} kr. højere end jeres likviditet til boligkøb. Aktierne er fredet, så I skal øge lånet.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"JOHAN (Pension fra {pensionsudbetalingsalder_j} år)")
        st.write(f"**Startdepot:** {int(depot_free_j + depot_ask_j):,} kr.")
        st.write(f"**Mdl. opsparing:** {int(inv_md_j):,} kr.")
        st.write(f"**FIRE udgift:** {int(fire_expenses_j):,} kr./md.")
    
    with col2:
        st.subheader(f"MARKUS (Pension fra {pensionsudbetalingsalder_m} år)")
        st.write(f"**Startdepot:** {int(depot_free_m + depot_ask_m):,} kr.")
        st.write(f"**Mdl. opsparing:** {int(inv_md_m):,} kr.")
        st.write(f"**FIRE udgift:** {int(fire_expenses_m):,} kr./md.")

    st.divider()

    table_data = []
    j_full_fire_reached, m_full_fire_reached = False, False
    j_fire_age, m_fire_age = 0, 0
    pension_at_target_j, pension_at_target_m = 0, 0

    for year in range(0, max_years + 1):
        current_age_j = age_j + year
        current_age_m = age_m + year

        if year > 0:
            if not j_full_fire_reached: depot_free_j += yearly_savings_j
            if not m_full_fire_reached: depot_free_m += yearly_savings_m

            ask_return_j = depot_ask_j * return_rate_gross
            depot_ask_j += ask_return_j - (ask_return_j * 0.17)
            free_return_j = depot_free_j * return_rate_gross
            free_tax_j = free_return_j * 0.27 if free_return_j <= progression_limit_j else (progression_limit_j * 0.27) + ((free_return_j - progression_limit_j) * 0.42)
            depot_free_j += free_return_j - free_tax_j

            ask_return_m = depot_ask_m * return_rate_gross
            depot_ask_m += ask_return_m - (ask_return_m * 0.17)
            free_return_m = depot_free_m * return_rate_gross
            free_tax_m = free_return_m * 0.27 if free_return_m <= progression_limit_m else (progression_limit_m * 0.27) + ((free_return_m - progression_limit_m) * 0.42)
            depot_free_m += free_return_m - free_tax_m

        total_depot_j_val = depot_ask_j + depot_free_j
        passive_j = calculate_drawdown_monthly_income(total_depot_j_val, current_age_j, pensionsudbetalingsalder_j, return_rate_net_drawdown)
        shortfall_j = max(0, fire_expenses_j - passive_j)
        hours_j = shortfall_j / (barista_wage_net * weeks_per_month)

        total_depot_m_val = depot_ask_m + depot_free_m
        passive_m = calculate_drawdown_monthly_income(total_depot_m_val, current_age_m, pensionsudbetalingsalder_m, return_rate_net_drawdown)
        shortfall_m = max(0, fire_expenses_m - passive_m)
        hours_m = shortfall_m / (barista_wage_net * weeks_per_month)

        table_data.append({
            "År": year,
            "J.alder": current_age_j,
            "J.depot (M)": f"{total_depot_j_val / 1_000_000:.2f}",
            "J.Passiv (kr)": f"{int(passive_j):,}",
            "J.Arbtid": get_emoji_status(hours_j),
            "M.alder": current_age_m,
            "M.depot (M)": f"{total_depot_m_val / 1_000_000:.2f}",
            "M.Passiv (kr)": f"{int(passive_m):,}",
            "M.Arbtid": get_emoji_status(hours_m)
        })

        if hours_j == 0 and not j_full_fire_reached:
            j_full_fire_reached = True
            j_fire_age = current_age_j
            pension_at_target_j = pension_j * ((1 + (return_rate_gross * (1 - pal_tax))) ** (pensionsudbetalingsalder_j - age_j))

        if hours_m == 0 and not m_full_fire_reached:
            m_full_fire_reached = True
            m_fire_age = current_age_m
            pension_at_target_m = pension_m * ((1 + (return_rate_gross * (1 - pal_tax))) ** (pensionsudbetalingsalder_m - age_m))

        if hours_j == 0 and hours_m == 0:
            break

        if year > 0:
            progression_limit_j *= (1 + inflation_rate)
            progression_limit_m *= (1 + inflation_rate)

    st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    if j_full_fire_reached:
        st.success(f"**Johans brofinansiering er sikret ved alder {j_fire_age}.** Pension forventes ca. {pension_at_target_j / 1_000_000:.2f}M kr.")
    if m_full_fire_reached:
        st.success(f"**Markus brofinansiering er sikret ved alder {m_fire_age}.** Pension forventes ca. {pension_at_target_m / 1_000_000:.2f}M kr.")

# UI Tabs for Scenarios
tab1, tab2, tab3, tab4 = st.tabs(["Plan A (4.0M)", "Plan B (4.5M)", "Plan C (5.0M)", "Plan D (Valby)"])

with tab1:
    simulate_joint_fire_plan("Plan A (4.0M Bolig)", 4000000, 1846222, 1153888, 4075, 4564, bolig_solgt=True)
with tab2:
    simulate_joint_fire_plan("Plan B (4.5M Bolig)", 4500000, 2250000, 1125000, 4576, 4564, bolig_solgt=True)
with tab3:
    simulate_joint_fire_plan("Plan C (5.0M Bolig)", 5000000, 2408888, 983888, 6519, 4564, bolig_solgt=True)
with tab4:
    simulate_joint_fire_plan("Plan D (Valby Nuværende)", 6700000, 0, 0, 15230, 4564, bolig_solgt=False)
