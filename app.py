import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIRE Dashboard", layout="wide")

# --- GLOBAL CSS (Claude-stil, men sikker) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Moderne og subtile brofinansieringskasser */
    .success-box {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        border-radius: 4px;
        padding: 12px 16px;
        color: #374151;
        font-size: 0.95em;
        margin-bottom: 10px;
    }
    @media (prefers-color-scheme: dark) {
        .success-box {
            background-color: #064e3b;
            border-left: 4px solid #34d399;
            color: #d1fae5;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("FIRE Brofinansiering: Johan & Markus")

# --- 1. SIDEBAR TIL INTERAKTIVE VARIABLER ---
st.sidebar.header("Globale Antagelser")
st.sidebar.markdown("Juster variablerne for at stress-teste alle scenarier samtidigt.")

global_return_rate_gross = st.sidebar.slider("Bruttoafkast under opsparing (%)", min_value=3.0, max_value=10.0, value=7.0, step=0.5) / 100
global_return_rate_net_drawdown = st.sidebar.slider("Nettoafkast i passiv fase (%)", min_value=2.0, max_value=8.0, value=4.5, step=0.1) / 100
global_inflation_rate = st.sidebar.slider("Årlig inflation (%)", min_value=0.0, max_value=5.0, value=2.0, step=0.5) / 100
global_barista_wage_net = st.sidebar.number_input("Baristaløn (Netto kr./t)", min_value=80, max_value=250, value=135, step=5)

st.sidebar.divider()

# --- STRESSTEST (KONSVERVATIV TILSTAND) ---
st.sidebar.markdown("### 🚨 Risikostyring")
conservative_mode = st.sidebar.toggle("Aktiver Konservativt Estimat")

if conservative_mode:
    # Overskriver slider-værdierne midlertidigt for at stresse modellen
    global_return_rate_gross = 0.05
    global_return_rate_net_drawdown = 0.03
    global_inflation_rate = 0.03
    st.sidebar.warning("Stresstest aktiv: Afkast sænket til 5% (brutto) / 3% (netto). Inflation hævet til 3%.")

st.sidebar.divider()
st.sidebar.markdown("💡 *Aktiedepoter (ASK + Frie midler) og Markus' BSU er fastlåst og holdt ude af boligfinansieringen i disse beregninger.*")

# --- BASIS DATA (Brugt i global visning) ---
inkomst_j, inkomst_m = 38468, 32983
pension_j, pension_m = 845000, 570000

# Opdateret formue (Johan: Friværdi + Særeje | Markus: Friværdi + Gældsnedbringelse)
cash_j_base = 2567500
cash_m_base = 1153888

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
    * **Lagerbeskatning:** ASK beskattes fladt med 17%. Frie midler beskattes progressivt (27% op til grænsen, 42% derover). Progressionsgrænsen indekseres årligt med inflationen.
    * **Inflationseffekt:** Udgifter, opsparingsrate og progressionsgrænser stiger alle med den valgte inflationsrate år for år i modellen.
    * **Pension adskilt:** Pensionsdepoter bruges *ikke* før 67 år. Indbetalinger stopper det år fuld FIRE nås, hvorefter depotet kun vokser med afkast minus PAL-skat (15,3%).
    * **Barista-timer:** Timer beregnes på *restbehovet*. Passiv indkomst fra depotet fratrækkes FIRE-udgifterne først.
    * **Dynamiske boligudgifter:** Bliver der optaget realkreditlån, indgår ydelsen fuldt ud i de månedlige FIRE-udgifter for det givne scenarie.
    * **Risiko - Inflation på udgifter:** FIRE-udgifterne fremskrives årligt. Nominelle kroner undervurderer systematisk fremtidige udgifter.
    * **Risiko - Folkepensionsmodregning:** Folkepension og pensionstillæg medregnes fra år 67, men tillægget reduceres ved formue/indkomst. Modellen anvender et konservativt skøn.
    """)

with st.expander("📊 Se Grunddata - Formue, Budget & Pension"):
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
