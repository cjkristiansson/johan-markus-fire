import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Brofinansiering", layout="wide")

# --- MODERNE UI & TYPOGRAFI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, .stApp { font-family: 'Inter', sans-serif !important; }
    .success-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 8px; color: #166534; font-size: 0.9em; margin-bottom: 10px; }
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #0c0c0c; }
        .success-box { background: #064e3b; border: 1px solid #065f46; color: #d1fae5; }
    }
</style>
""", unsafe_allow_html=True)

st.title("FIRE Brofinansiering: Johan & Markus")

# --- SIDEBAR ---
st.sidebar.header("Globale Antagelser")
global_return_rate_gross = st.sidebar.slider("Bruttoafkast (%)", 3.0, 10.0, 7.0, 0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast (Passiv) (%)", 2.0, 8.0, 4.5, 0.1) / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", 0.0, 5.0, 2.0, 0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", 80, 250, 135, 5)

# --- DATA ---
cash_j_base, cash_m_base = 2567500, 1153888
basis_ask_j, basis_frie_j = 174000, 71000
basis_ask_m, basis_frie_m = 170000, 0
budget_j = {"Studielaan": 0, "Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1674, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
budget_m = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 720, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

# --- ACCORDIONS ---
with st.expander("⚙️ Modellens Regler & Logik"):
    st.markdown("- Startdepot = Formue efter bolig. Aktier låst til FIRE.\n- Skat: ASK (17%), Frie midler progressivt (27/42%).\n- Inflation: Udgifter/opsparing indekseres årligt.")

with st.expander("📊 Grunddata & Budget"):
    c1, c2 = st.columns(2)
    c1.markdown("### Johan\n**Løn:** 38.468 kr. **Pension:** 845.000 kr.\n" + "\n".join([f"- {k}: {v} kr." for k,v in budget_j.items() if v > 0]))
    c2.markdown("### Markus\n**Løn:** 32.983 kr. **Pension:** 570.000 kr.\n" + "\n".join([f"- {k}: {v} kr." for k,v in budget_m.items() if v > 0]))

# --- LOGIK ---
def calculate_drawdown(depot, cur_age, target_age, rate):
    if cur_age >= target_age: return 0
    months = (target_age - cur_age) * 12
    m_rate = rate / 12
    return depot * (m_rate * (1 + m_rate)**months) / ((1 + m_rate)**months - 1)

def simulate(name, boligpris, udbet_j, udbet_m, realkredit, ejerudgift, bolig_solgt):
    c_j = cash_j_base if bolig_solgt else 0
    c_m = cash_m_base if bolig_solgt else 0
    faktisk_m = udbet_m - max(0, udbet_m - c_m)
    faktisk_j = (udbet_j + max(0, udbet_m - c_m)) - max(0, (udbet_j + max(0, udbet_m - c_m)) - c_j)
    
    depot_j = basis_ask_j + basis_frie_j + (c_j - faktisk_j)
    depot_m = basis_ask_m + basis_frie_m + (c_m - faktisk_m)
    bolig_faelles = (realkredit + ejerudgift) / 2
    
    st.markdown(f"**Udbetaling (J/M):** {int(faktisk_j):,} / {int(faktisk_m):,} kr. | **Realkredit (egen del):** {int(realkredit/2):,} kr./md. | **Startdepot (J/M):** {int(depot_j):,} / {int(depot_m):,} kr.")
    
    data = []
    e_j = sum(v for k, v in budget_j.items() if k not in ["A_kasse_Fagforening", "Loensikring"]) + bolig_faelles
    e_m = sum(v for k, v in budget_m.items() if k not in ["A_kasse_Fagforening", "Loensikring", "Studielaan"]) + bolig_faelles
    
    for y in range(0, 26):
        age_j, age_m = 41 + y, 32 + y
        p_j = calculate_drawdown(depot_j, age_j, 67, global_return_rate_net_drawdown)
        p_m = calculate_drawdown(depot_m, age_m, 67, global_return_rate_net_drawdown)
        
        # Beregn arbejdshuller
        h_j = max(0, e_j - p_j) / (global_barista_wage_net * 4.33)
        h_m = max(0, e_m - p_m) / (global_barista_wage_net * 4.33)
        
        data.append({"År": y, "J.alder": age_j, "J.depot (M)": f"{depot_j/1e6:.2f}", "J.Passiv": int(p_j), "J.Arbtid": f"{h_j:.1f}t", "M.alder": age_m, "M.depot (M)": f"{depot_m/1e6:.2f}", "M.Passiv": int(p_m), "M.Arbtid": f"{h_m:.1f}t"})
        
        # Vækst (simuleret)
        depot_j *= (1 + global_return_rate_gross)
        depot_m *= (1 + global_return_rate_gross)
        e_j *= (1 + global_inflation_rate)
        e_m *= (1 + global_inflation_rate)
        
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["Plan A", "Plan B", "Plan C", "Plan D"])
with t1: simulate("Plan A", 4000000, 1846222, 1153888, 4075, 4564, True)
with t2: simulate("Plan B", 4500000, 2250000, 1125000, 4576, 4564, True)
with t3: simulate("Plan C", 5000000, 2408888, 983888, 6519, 4564, True)
with t4: simulate("Plan D", 6700000, 0, 0, 15230, 4564, False)
