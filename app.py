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
    
    /* Moderne Success-boks */
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

st.title("FIRE Brofinansiering")

# --- SIDEBAR ---
st.sidebar.header("Globale Antagelser")
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

# --- ACCORDIONS ---
with st.expander("⚙️ Modellens Regler & Logik"):
    st.markdown("Herunder findes de matematiske principper for simuleringen.")
    
with st.expander("📊 Grunddata & Budget"):
    col1, col2 = st.columns(2)
    col1.markdown(f"### Johan\n**Løn:** {inkomst_j:,} kr.\n**Budget:** {format_budget(budget_j)}".replace(',', '.'))
    col2.markdown(f"### Markus\n**Løn:** {inkomst_m:,} kr.\n**Budget:** {format_budget(budget_m)}".replace(',', '.'))

# --- LOGIK & SIMULERING (Samme som før) ---
# (Bemærk: Jeg har beholdt din eksisterende logik indeni simulate_joint_fire_plan)

# --- TAB-SYSTEMET ---
tab1, tab2, tab3, tab4 = st.tabs(["Plan A (4.0M)", "Plan B (4.5M)", "Plan C (5.0M)", "Plan D (Valby)"])

# ... (Her indsætter du simulate_joint_fire_plan kaldene som før)
