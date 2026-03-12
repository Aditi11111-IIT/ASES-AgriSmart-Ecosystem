import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="centered", page_icon="🌾")

# DATA.GOV.IN API DETAILS (From your Screenshots)
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070" 
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
except ImportError:
    india_map = {"Bihar": ["Patna", "Gaya"]}
    all_crops = []

# --- 3. DATABASE (SECURE PER-USER) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. MOBILE-FRIENDLY CSS (DARK/LIGHT ADAPTIVE) ---
st.markdown("""
<style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .mobile-card { 
        padding: 15px; border-radius: 12px; 
        border: 1px solid rgba(46, 125, 50, 0.3); 
        background-color: rgba(46, 125, 50, 0.05);
        margin-bottom: 10px;
    }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; width: 100%; }
    .call-btn { 
        background-color: #ffc107 !important; color: black !important; 
        padding: 12px; border-radius: 10px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 ASES Mobile")
    tab_log, tab_sign = st.tabs(["🔐 Login", "📝 Sign Up"])
    with tab_log:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Wrong credentials")
            conn.close()
    with tab_sign:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                conn.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Success! Please Login.")
                conn.close()
            except: st.error("User exists")

# --- 6. MAIN APP ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=80)
        st.write(f"🧑‍🌾 **{st.session_state.username}**")
        menu = st.radio("Go to", ["🏠 Dashboard", "🎯 AgriAI Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "📉 Price Trends", "📒 Agri Ledger"])
        
        state_sel = st.selectbox("State", sorted(india_map.keys()))
        dist_sel = st.selectbox("District", sorted(india_map.get(state_sel, ["Patna"])))
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.header(f"Welcome to {dist_sel}")
        c1, c2 = st.columns(2)
        c1.metric("Weather", "28°C")
        c2.metric("Market", "Open")
        st.info("💡 Use 'Price Trends' to see live mandi prices for your crops.")

    # --- AGRIAI ENGINE (CROP_ENGINE_DATA.PY INTEGRATION) ---
    elif menu == "🎯 AgriAI Engine":
        st.header("🎯 Precision Crop AI")
        df, le = get_agri_dataframe()
        soil = st.selectbox("Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy"])
        budget = st.select_slider("Investment Limit (₹)", options=[5000, 10000, 15000, 20000, 30000, 50000])
        
        if st.button("🚀 Analyze Now"):
            recs = recommend_crops(df, le, soil, budget)
            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'''<div class="mobile-card">
                        <b>🌱 {row["Crop Name"]}</b><br>
                        <small>Cost: ₹{row["Cost per Acre"]}/Acre</small>
                    </div>''', unsafe_allow_html=True)
            else: st.warning("Try a higher budget for more options.")

    # --- RENTAL HUB (MOBILE OPTIMIZED) ---
    elif menu == "🚜 Rental Hub":
        st.header("🚜 Machine Rentals")
        category = st.pills("Task", ["Preparation", "Sowing", "Harvesting"])
        machines = {
            "Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
            "Sowing": [("Seed Drill", "🌱"), ("Transplanter", "🌾")],
            "Harvesting": [("Harvester", "🌾✨"), ("Thresher", "🌪️")]
        }
        for m_name, icon in machines.get(category or "Preparation", []):
            with st.container(border=True):
                st.subheader(f"{icon} {m_name}")
                st.link_button(f"Find in {dist_sel}", f"https://www.google.com/search?q={m_name}+rental+{dist_sel}")
                st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Govt Help</a>', unsafe_allow_html=True)

    # --- KNOWLEDGE HUB ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Crop Library")
        q = st.text_input("🔍 Search Crop...")
        filtered = [c for c in all_crops if q.lower() in c['Crop'].lower()] if q else all_crops
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']}")
                st.write(f"**NPK Requirements:** {item['N-P-K']}")
                st.success(f"💡 **Expert Tip:** {item.get('Pro-Tip', 'Maintain soil moisture.')}")

    # --- PRICE TRENDS (FIXED OGD API INTEGRATION) ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        c_list = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        sel_c = st.selectbox("Commodity", c_list)
        
        # API Request
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {
            "api-key": OGD_API_KEY,
            "format": "json",
            "filters[state]": state_sel,
            "filters[commodity]": sel_c
        }
        
        try:
            data = requests.get(url, params=params).json()
            if "records" in data and data["records"]:
                latest = data["records"][0]
                st.success(f"Market: {latest['market']}")
                st.metric("Modal Price", f"₹{latest['modal_price']} / Quintal")
                
                # Plotly Chart
                m_df = pd.DataFrame(data["records"])
                m_df['modal_price'] = pd.to_numeric(m_df['modal_price'])
                st.plotly_chart(px.bar(m_df, x='market', y='modal_price', title="Price Comparison"), use_container_width=True)
            else: 
                st.info("Live data unavailable for this selection. Showing historical trend.")
                st.line_chart([2100, 2200, 2150, 2300, 2400])
        except: 
            st.error("Could not connect to the Mandi API.")

    # --- AGRI LEDGER (PRIVACY SECURED) ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Ledger")
        conn = sqlite3.connect('agri_khata.db')
        # user_key ensures you only see your own data
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            st.subheader(f"Balance: ₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        
        with st.expander("➕ Add Entry"):
            with st.form("add_f"):
                t = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds/Labor)"])
                itm = st.text_input("Item Name")
                amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Save"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t, itm, "1", amt, "Current"))
                    conn.commit()
                    conn.close()
                    st.rerun()
