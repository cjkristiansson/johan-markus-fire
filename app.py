import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

# --- CSS OG DATA INITIALISERING ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError: pass

load_css("style.css")

if "inkomst_j" not in st.session_state: st.session_state["inkomst_j"] = 38468
if "inkomst_m" not in st.session_state: st.session_state["inkomst_m"] = 32983
if "pension_j" not in st.session_state: st.session_state["pension_j"] = 845000
if "pension_m" not in st.session_state: st.session_state["pension_m"] = 570000
if "cash_j_base" not in st.session_state: st.session_state["cash_j_base"] = 2567500
if "cash_m_base" not in st.session_state: st.session_state["cash_m_base"] = 1153888
if "basis_ask_j" not in st.session_state: st.session_state["basis_ask_j"] = 174000
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 65000
if "basis_ask_m" not in st.session_state: st.session_state["basis_ask_m"] = 170000
if "basis_frie_m" not in st.session_state: st.session_state["basis_frie_m"] = 0
if "budget_j" not in st.session_state:
    st.session_state["budget_j"] = {"Mad": 6000, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 672, "Loensikring": 1674, "Puregym": 279, "Transport": 730, "Telefon": 100, "Spotify_Cloud": 100, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}
if "budget_m" not in st.session_state:
    st.session_state["budget_m"] = {"Studielaan": 1600, "Mad": 0, "Ferie": 1500, "Renovering": 1000, "A_kasse_Fagforening": 520, "Loensikring": 720, "Puregym": 0, "Transport": 500, "Telefon": 300, "Streaming": 565, "Charity": 100, "Frisoer": 450, "Toej": 1200, "Oevrig": 3000}

# --- FUNKTIONER ---
def calculate_drawdown(depot, age, target_age, return_rate):
    if age >= target_age: return 0
    months = (target_age - age) * 12
    rate = return_rate / 12
    return depot * (rate * (1 + rate)**months) / ((1 + rate)**months - 1) if rate > 0 else depot / months

def get_emoji(hours):
    if hours <= 0: return "🟢 0.0t"
    if hours <= 15: return f"🟡 {hours:.1f}t"
    return f"🔴 {hours:.1f}t"

def simulate_joint_fire_plan(name, pris, udb_j, udb_m, ydelse, ejer, bolig_solgt):
    age_j, age_m, pal = 41, 32, 0.153
    cash_j = st.session_state["cash_j_base"] if bolig_solgt else 0
    cash_m = st.session_state["cash_m_base"] if bolig_solgt else 0
    depot_j = st.session_state["basis_frie_j"] + (cash_j - min(udb_j, cash_j))
    depot_m = st.session_state["basis_frie_m"] + (cash_m - min(udb_m, cash_m))
    ask_j, ask_m = st.session_state["basis_ask_j"], st.session_state["basis_ask_m"]
    
    bolig_total = (ydelse + ejer) / 2
    inv_j = (st.session_state["inkomst_j"] * 12) - (sum(st.session_state["budget_j"].values()) * 12 + bolig_total * 12)
    inv_m = (st.session_state["inkomst_m"] * 12) - (sum(st.session_state["budget_m"].values()) * 12 + bolig_total * 12)
    fire_j = sum(v for k, v in st.session_state["budget_j"].items() if k not in ["A_kasse_Fagforening"]) + bolig_total
    fire_m = sum(v for k, v in st.session_state["budget_m"].items() if k not in ["A_kasse_Fagforening"]) + bolig_total

    data = []
    for y in range(26):
        if y > 0:
            fire_j *= (1 + global_inflation_rate); fire_m *= (1 + global_inflation_rate)
            # Rigtig rækkefølge: Afkast på eksisterende, derefter tilføj opsparing
            depot_j = (depot_j * (1 + global_return_rate_gross * 0.73)) + (inv_j * (1 + global_inflation_rate)**y)
            depot_m = (depot_m * (1 + global_return_rate_gross * 0.73)) + (inv_m * (1 + global_inflation_rate)**y)
            ask_j *= (1 + global_return_rate_gross * 0.83); ask_m *= (1 + global_return_rate_gross * 0.83)
        
        p_j = calculate_drawdown(depot_j + ask_j, age_j + y, 67, global_return_rate_net_drawdown)
        p_m = calculate_drawdown(depot_m + ask_m, age_m + y, 65, global_return_rate_net_drawdown)
        h_j = max(0, fire_j - (p_j/12)) / (global_barista_wage_net * 4.33)
        h_m = max(0, fire_m - (p_m/12)) / (global_barista_wage_net * 4.33)
        data.append({"År": y, "J.alder": age_j + y, "J.Depot": f"{(depot_j+ask_j)/1e6:.2f}M", "J.Arb": get_emoji(h_j), "M.alder": age_m + y, "M.Depot": f"{(depot_m+ask_m)/1e6:.2f}", "M.Arb": get_emoji(h_m)})
    st.table(pd.DataFrame(data).set_index("År"))

def simulate_solo_fire_plan(name, pris, udbetaling, ydelse, ejer):
    age, cash = 41, st.session_state["cash_j_base"]
    depot = st.session_state["basis_frie_j"] + (cash - min(udbetaling, cash))
    ask = st.session_state["basis_ask_j"]
    budget = st.session_state["budget_j"].copy()
    budget["Mad"] = 3000
    inv = (st.session_state["inkomst_j"] * 12) - (sum(budget.values()) * 12 + (ydelse + ejer) * 12)
    fire_exp = sum(v for k, v in budget.items() if k not in ["A_kasse_Fagforening"]) + ydelse + ejer

    data = []
    for y in range(26):
        if y > 0:
            fire_exp *= (1 + global_inflation_rate)
            depot = (depot * (1 + global_return_rate_gross * 0.73)) + (inv * (1 + global_inflation_rate)**y)
            ask *= (1 + global_return_rate_gross * 0.83)
        passive = calculate_drawdown(depot + ask, age + y, 67, global_return_rate_net_drawdown)
        hours = max(0, fire_exp - (passive/12)) / (global_barista_wage_net * 4.33)
        data.append({"År": y, "Alder": age + y, "Depot": f"{(depot+ask)/1e6:.2f}M", "Passiv": int(passive/12), "Arbejde": get_emoji(hours)})
    st.table(pd.DataFrame(data).set_index("År"))

# --- UI LOGIK ---
st.sidebar.header("Globale Antagelser")
global_return_rate_gross = st.sidebar.slider("Bruttoafkast (%)", 3.0, 10.0, 7.0, 0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast passiv (%)", 2.0, 8.0, 4.5, 0.1) / 100
global_inflation_rate = st.sidebar.slider("Inflation (%)", 0.0, 5.0, 2.0, 0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto)", value=135)
st.sidebar.divider()
st.sidebar.text_input("Gendan Scenarie-ID", key="secret_id")

if st.sidebar.button("System", type="primary"):
    st.session_state["is_solo_mode"] = not st.session_state.get("is_solo_mode", False)
    st.rerun()

is_solo = st.session_state.get("is_solo_mode", False) or st.session_state.get("secret_id", "") == "solo"
tabs = st.tabs(["3.5M", "4.0M", "4.5M", "5.0M", "5.5M", "Valby"] + (["🔒 Solo 3.0M", "🔒 Solo 3.5M", "🔒 Solo 4.0M"] if is_solo else []))

with tabs[0]:
    yd = st.number_input("Ydelse 3.5M", value=8516, key="y35")
    st.markdown("**Specifikationer:** 3.5M køb, 40% udbetaling.")
    simulate_joint_fire_plan("3.5M", 3500000, 966000, 434000, yd, 4564, True)
with tabs[4]:
    yd55 = st.number_input("Ydelse 5.5M", value=13659, key="y55")
    st.markdown("**Specifikationer:** 5.5M køb, 40% udbetaling.")
    simulate_joint_fire_plan("5.5M", 5500000, 1515000, 685000, yd55, 4564, True)
