import streamlit as st
import pandas as pd

# --- INITIALISERING ---
st.set_page_config(page_title="FIRE Dashboard", layout="wide")
if "is_solo_mode" not in st.session_state: st.session_state["is_solo_mode"] = False
if "inkomst_j" not in st.session_state: st.session_state["inkomst_j"] = 38468
if "cash_j_base" not in st.session_state: st.session_state["cash_j_base"] = 2567500
if "basis_frie_j" not in st.session_state: st.session_state["basis_frie_j"] = 65000
if "budget_j" not in st.session_state: st.session_state["budget_j"] = {"Mad": 6000, "Oevrig": 3000}

# --- HJÆLPEFUNKTIONER ---
def calculate_drawdown(depot, age, target_age, return_rate):
    if age >= target_age: return 0
    months = (target_age - age) * 12
    rate = return_rate / 12
    return depot * (rate * (1 + rate)**months) / ((1 + rate)**months - 1) if rate > 0 else depot / months

def simulate_solo_fire_plan(boligpris, udbetaling, ydelse, ejer):
    age = 41
    cash = st.session_state["cash_j_base"]
    depot = st.session_state["basis_frie_j"] + (cash - min(udbetaling, cash))
    budget = st.session_state["budget_j"].copy()
    budget["Mad"] = 3000
    
    start_inv = st.session_state["inkomst_j"] - (sum(budget.values()) + ydelse + ejer)
    fire_exp = sum(v for k, v in budget.items() if k not in ["A_kasse_Fagforening"]) + ydelse + ejer

    data = []
    for y in range(26):
        if y > 0:
            fire_exp *= 1.02
            depot += (start_inv * 12) * (1.02**y)
            depot *= 1.05 # Groft afkast
        passive = calculate_drawdown(depot, age + y, 67, 0.04)
        data.append({"År": y, "Alder": age + y, "Depot": f"{depot/1e6:.2f}M", "Passiv": int(passive)})
    st.table(pd.DataFrame(data))

# --- SIDEBAR (MED USYNLIG TRIGGER) ---
with st.sidebar:
    st.markdown('<div class="secret-trigger" onclick="window.location.reload()"></div>', unsafe_allow_html=True)
    if st.button("Aktiver Solo-tilstand", key="trigger"):
        st.session_state["is_solo_mode"] = not st.session_state["is_solo_mode"]
        st.rerun()

# --- SCENARIER ---
tab_names = ["3.5M", "4.0M", "4.5M", "5.0M", "5.5M"]
if st.session_state["is_solo_mode"]: tab_names.extend(["🔒 Solo 3.0M", "🔒 Solo 3.5M"])
tabs = st.tabs(tab_names)

with tabs[0]:
    yd = st.number_input("Ydelse 3.5M", value=8516)
    st.write("Specifikationer for 3.5M lånet...")
    # ... kald simulate funktion ...
