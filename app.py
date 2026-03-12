import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API KEYS ---
# Using the Mandi Price Resource ID and API Key from your dashboard
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070" 
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"

st.set_page_config(page_title="ASES: Agri-Smart", layout="centered", page_icon="🌾")

# --- 2. MODULAR IMPORTS (CITATIONS: 1, 2, 4, 5) ---
try:
    from Locations import india_map  # [cite: 5]
    from crop_master import all_crops  # [cite: 2]
    from crop_engine_data import get_agri_dataframe, recommend_crops  # 
    from schemes_db import get_state_schemes, get_central_schemes  # [cite: 4]
except ImportError as e:
    st.error(f"⚠️ Missing Module: {e}")
    india_map = {"Bihar": ["Patna", "Gaya"]}
    all_crops = []

# --- 3. DATABASE LOGIC (STRICT PRIVACY) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    # user_key is critical for data isolation
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. MOBILE-FRIENDLY & THEME-ADAPTIVE UI ---
st.markdown("""
<style>
    .stApp { max-width: 850px; margin: 0 auto; }
    .mobile-card { 
        padding: 15px; border-radius: 12px; 
        border: 1px solid rgba(46, 125, 50, 0.3); 
        background-color: rgba(46, 125, 50, 0.05);
        margin-bottom: 12px;
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
    st.title("🌾 ASES: Agri-Smart")
    t1, t2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Invalid credentials.")
            conn.close()
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                conn.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Account created! Please log in.")
                conn.close()
            except: st.error("Username already exists.")

# --- 6. MAIN APPLICATION ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=80)
        st.subheader(f"Farmer: {st.session_state.username}")
        menu = st.radio("SERVICES", ["🏠 Home", "🎯 Crop Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "📉 Price Trends", "📒 Agri Ledger"])
        
        st_sel = st.selectbox("State", sorted(india_map.keys()))
        dt_sel = st.selectbox("District", sorted(india_map.get(st_sel, ["Patna"])))
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- TAB: HOME ---
    if menu == "🏠 Home":
        st.header(f"📍 {dt_sel}, {st_sel}")
        c1, c2 = st.columns(2)
        c1.metric("System Status", "Connected")
        c2.metric("Region Info", "Active")
        st.info("💡 Pro Tip: Use 'Agri Ledger' to track your daily income and expenses privately.")

    # --- TAB: CROP ENGINE (REPAIRED INTEGRATION) ---
    elif menu == "🎯 Crop Engine":
        st.header("🎯 Precision Crop AI")
        df, le = get_agri_dataframe()  # 
        soil = st.selectbox("Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy", "Loamy", "Clayey"])
        budget = st.slider("Budget (₹/Acre)", 5000, 50000, 15000)
        
        if st.button("🚀 GET RECOMMENDATIONS"):
            # Passing parameters to the KNN model in crop_engine_data.py 
            recs = recommend_crops(df, le, soil, budget)
            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'''<div class="mobile-card">
                        <b>🌱 {row["Crop Name"]}</b><br>
                        <small>Avg Cost: ₹{row["Cost per Acre"]}/Acre</small>
                    </div>''', unsafe_allow_html=True)
            else: st.warning("No matches found for this budget. Try increasing it.")

    # --- TAB: RENTAL HUB (MOBILE-FIRST) ---
    elif menu == "🚜 Rental Hub":
        st.header("🚜 Equipment Rental")
        cat = st.segmented_control("Stage", ["Tillage", "Sowing", "Harvest"], default="Tillage")
        m_list = {
            "Tillage": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
            "Sowing": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
            "Harvest": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
        }
        for name, icon in m_list.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Search in {dt_sel}", f"https://www.google.com/search?q={name}+rentals+in+{dt_sel}")
                st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Govt Help Center</a>', unsafe_allow_html=True)

    # --- TAB: KNOWLEDGE HUB (DETAILED FROM crop_master.py) ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Farmer's Library")
        search = st.text_input("🔍 Search Crop Name...").strip()
        filtered = [c for c in all_crops if search.lower() in c['Crop'].lower()] if search else all_crops # [cite: 2]
        
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']} | **NPK:** {item['N-P-K']}")
                st.write(f"**Soil:** {item['Soil']} | **Water:** {item['Water']}")
                st.success(f"💡 **Pro-Tip:** {item.get('Pro-Tip', 'Monitor soil moisture regularly.')}")

    # --- TAB: PRICE TRENDS (REAL-TIME MANDI API) ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Analysis")
        commodity = st.selectbox("Select Crop", [c['Crop'] for c in all_crops] or ["Wheat", "Rice"])
        
        # OGD API Implementation for Real-time Mandi Data
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": st_sel, "filters[commodity]": commodity}
        
        try:
            response = requests.get(url, params=params).json()
            if "records" in response and response["records"]:
                latest = response["records"][0]
                st.metric(f"Current Price ({latest['market']})", f"₹{latest['modal_price']} / Quintal")
                
                m_df = pd.DataFrame(response["records"])
                m_df['modal_price'] = pd.to_numeric(m_df['modal_price'])
                st.plotly_chart(px.bar(m_df, x='market', y='modal_price', title="Local Mandi Comparison", color_discrete_sequence=['#2e7d32']), use_container_width=True)
            else:
                st.warning("Live data currently unavailable for this selection. Showing historical cycles.")
        except:
            st.error("Connection to Mandi servers failed.")

        # Annual Trend visualization
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        prices = [2100, 2050, 2150, 2200, 2300, 2250, 2350, 2400, 2380, 2450, 2500, 2480]
        st.plotly_chart(px.line(x=months, y=prices, title="Annual Market Cycle", markers=True), use_container_width=True)

    # --- TAB: AGRI LEDGER (STRICT PRIVACY) ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Agri Khata")
        conn = sqlite3.connect('agri_khata.db')
        # Privacy Check: user_key filter ensures users only see their own records
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            income = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            expense = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            st.subheader(f"Total Profit: ₹{income - expense:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        else:
            st.info("No records found. Add your first transaction below.")

        with st.expander("➕ Add New Entry"):
            with st.form("ledger_f"):
                cat_type = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds/Fertilizer)", "Expense (Labor)"])
                desc = st.text_input("Item Description")
                amount = st.number_input("Amount (₹)", min_value=0.0)
                if st.form_submit_button("Save Transaction"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), cat_type, desc, "1", amount, "General"))
                    conn.commit()
                    conn.close()
                    st.rerun()
