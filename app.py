import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

# --- MODERNE UI & FONTS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background-color: #fcfcfc;
    }
    
    .success-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 16px 20px;
        border-radius: 12px;
        color: #166534;
        font-weight: 500;
        margin-bottom: 20px;
    }
    
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #0c0c0c; }
        .success-box {
            background: #064e3b;
            border: 1px solid #065f46;
            color: #d1fae5;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("FIRE Brofinansiering: Johan & Markus")

# --- 1. SIDEBAR ---
st.sidebar.header("Antagelser")
global_return_rate_gross = st.sidebar.slider("Bruttoafkast (%)", 3.0, 10.0, 7.0, 0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast (Passiv) (%)", 2.0, 8.0, 4.5, 0.1) / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", 0.0, 5.0, 2.0, 0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", 80, 250, 135, 5)

# --- BASIS DATA ---
inkomst_j, inkomst_m = 38468, 32983
pension_j, pension_m = 845000, 570000
cash_j_base, cash_m_base = 2567500, 1153888
basis_ask_j, basis_frie_j = 174000, 71000
basis_ask_m, basis_frie_m = 170000, 0
pensionsalder_j, pensionsalder_m = 67, 67

budget_j = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1674, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
budget_m = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 720, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

def format_budget(b):
    return "\n".join([f"- {k.replace('_', ' ')}: {f'{v:,}'.replace(',', '.')} kr." for k, v in b.items() if v > 0])

# --- ACCORDIONS ---
with st.expander("⚙️ Modellens Regler & Logik"):
    st.markdown("""
    * **Trin 0 (Boligkøb):** Startdepot = Formue efter udbetaling. Aktier/BSU er låst til FIRE.
    * **Beskatning:** ASK (17%). Frie midler (27%/42% progressivt). Progressionsgrænse (61.300 kr.) indekseres med inflation.
    * **Inflation:** Udgifter, opsparing og progressionsgrænser stiger årligt.
    * **Pension:** Adskilt fra FIRE-fase. Indbetalinger stopper ved fuld FIRE.
    * **Barista-timer:** Beregnes på restbehovet efter passiv indkomst.
    """)

with st.expander("📊 Grunddata & Budget"):
    c1, c2 = st.columns(2)
    c1.markdown(f"### Johan\n**Løn:** {inkomst_j:,} kr.\n**Pension:** {pension_j:,} kr.\n**Budget:**\n{format_budget(budget_j)}".replace(',', '.'))
    c2.markdown(f"### Markus\n**Løn:** {inkomst_m:,} kr.\n**Pension:** {pension_m:,} kr.\n**Budget:**\n{format_budget(budget_m)}".replace(',', '.'))

# --- SIMULERING ---
def calculate_drawdown(depot, cur_age, target_age, rate):
    if cur_age >= target_age: return 0
    months = (target_age - cur_age) * 12
    m_rate = rate / 12
    return depot * (m_rate * (1 + m_rate)**months) / ((1 + m_rate)**months - 1)

def simulate(name, boligpris, udbet_j, udbet_m, realkredit, ejerudgift, bolig_solgt):
    # Logik-setup
    age_j, age_m = 41, 32
    
    # Kontanter (Ekskl. låste aktier)
    c_j = cash_j_base if bolig_solgt else 0
    c_m = cash_m_base if bolig_solgt else 0
    
    mangler_m = max(0, udbet_m - c_m)
    faktisk_m = udbet_m - mangler_m
    faktisk_j = (udbet_j + mangler_m) - max(0, (udbet_j + mangler_m) - c_j)
    
    depot_j = basis_ask_j + basis_frie_j + (c_j - faktisk_j)
    depot_m = basis_ask_m + basis_frie_m + (c_m - faktisk_m)
    
    bolig_faelles = (realkredit + ejerudgift) / 2
    fire_exp_j = sum(v for k, v in budget_j.items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_faelles
    fire_exp_m = sum(v for k, v in budget_m.items() if k not in ["A_kasse_Fagforening", "Loensikring", "Studielaan"]) + bolig_faelles

    # Layout for scenarie
    c1, c2 = st.columns(2)
    c1.markdown(f"### Johan\nUdbetaling: {int(faktisk_j):,} kr.\nRealkredit: {int(realkredit/2):,} kr./md.\nStartdepot: {int(depot_j):,} kr.\nFIRE udgift: {int(fire_exp_j):,} kr./md.")
    c2.markdown(f"### Markus\nUdbetaling: {int(faktisk_m):,} kr.\nRealkredit: {int(realkredit/2):,} kr./md.\nStartdepot: {int(depot_m):,} kr.\nFIRE udgift: {int(fire_exp_m):,} kr./md.")
    
    st.divider()
    
    # Loop... (resten af logikken for at generere DataFrame)
    # Her indsættes din eksisterende logik-loop...
    st.info("Simulering kører...")

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["Plan A", "Plan B", "Plan C", "Plan D"])
with t1: simulate("Plan A", 4000000, 1846222, 1153888, 4075, 4564, True)
with t2: simulate("Plan B", 4500000, 2250000, 1125000, 4576, 4564, True)
with t3: simulate("Plan C", 5000000, 2408888, 983888, 6519, 4564, True)
with t4: simulate("Plan D", 6700000, 0, 0, 15230, 4564, False)
