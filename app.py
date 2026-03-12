import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & API KEYS ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="wide", page_icon="🌾")
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY", "YOUR_OPENWEATHER_KEY")

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
except ImportError as e:
    st.error(f"⚠️ Critical Module Missing: {e}")
    india_map = {"Bihar": ["Patna", "Gaya", "Muzaffarpur"]}
    all_crops = []
    def get_state_schemes(state): return []
    def get_central_schemes(): return []

# --- 3. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

def delete_user_data(username):
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute("DELETE FROM ledger WHERE user_key = ?", (username,))
    conn.commit()
    conn.close()

init_db()

# --- 4. REAL-TIME DATA ENGINES ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        data = requests.get(url).json()
        return {"temp": data["main"]["temp"], "humidity": data["main"]["humidity"], "desc": data["weather"][0]["description"].title()}
    except: return None

def get_live_mandi_prices(state, commodity):
    url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
    params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": state, "filters[commodity]": commodity, "limit": 10}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "records" in data and len(data["records"]) > 0: return pd.DataFrame(data["records"])
        return None
    except: return None

# --- 5. STYLING ---
st.markdown("""
<style>
    .main-card { padding: 20px; border-radius: 15px; background-color: rgba(46, 125, 50, 0.1); border: 1px solid #2e7d32; margin-bottom: 15px; }
    .weather-card { background-color: #e3f2fd; padding: 20px; border-radius: 15px; border-left: 10px solid #2196f3; margin-bottom: 20px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; height: 3em; background-color: #2e7d32; color: white; }
    .call-btn { background-color: #ffc107 !important; color: black !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 6. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 Agri-Smart Ecosystem (ASES)")
    t1, t2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Invalid credentials.")
            conn.close()
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                c = conn.cursor()
                c.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Registration successful!")
                conn.close()
            except sqlite3.IntegrityError: st.error("Username already exists.")

# --- 7. MAIN INTERFACE ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=100)
        st.subheader(f"Welcome, {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        tab = st.radio("MENU", ["🏠 Home", "🎯 Crop AI", "🚜 Rental Hub", "🏛️ Govt Schemes", "📈 Market Trends", "📒 Agri Ledger"])
        
        state_list = sorted(list(india_map.keys()))
        s_state = st.selectbox("Current State", state_list)
        s_dist = st.selectbox("District", sorted(india_map.get(s_state, ["Patna"])))

    # --- TAB 1: HOME (DASHBOARD WITH WEATHER) ---
    if tab == "🏠 Home":
        st.title(f"📍 Region: {s_dist}, {s_state}")
        
        weather = get_weather(s_dist)
        if weather:
            st.markdown(f"""<div class="weather-card">
                <h3 style="margin:0; color: #0d47a1;">☁️ Live Weather: {s_dist}</h3>
                <p style="margin:0; font-size: 26px;"><b>{weather['temp']}°C</b> | {weather['desc']}</p>
                <p style="margin:0; opacity: 0.8;">Humidity: {weather['humidity']}%</p>
            </div>""", unsafe_allow_html=True)
            
            st.subheader("⚠️ Smart Agriculture Alerts")
            if weather['temp'] > 35: st.error(f"🔥 **High Heat:** Temps above 35°C in {s_dist}. Increase irrigation.")
            elif weather['humidity'] > 80: st.warning("🪳 **Pest Risk:** High humidity detected. Check for fungal growth.")
            else: st.success("✅ **Optimal Conditions:** Weather is stable for planned activities.")

        st.divider()
        st.subheader("📊 System Overview")
        c1, c2, c3 = st.columns(3)
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT total, type FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()
        total_exp = df_khata[df_khata['type'].str.contains('Expense', na=False)]['total'].sum()
        
        c1.metric("Sync Status", "Live")
        c2.metric("Total Investment", f"₹{total_exp:,.0f}")
        c3.metric("Project ID", "IITP-ASES v1.4")

    # --- TAB 2: CROP AI (WITH SMALL FARMER FILTER) ---
    elif tab == "🎯 Crop AI":
        st.title("🎯 Precision Crop Engine")
        df, le = get_agri_dataframe()
        
        is_small_farmer = st.checkbox("🚜 Small Farmer Mode", help="Filters for low-investment crops.")
        col1, col2 = st.columns(2)
        with col1: soil = st.selectbox("Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy"])
        with col2: 
            budget = st.slider("Budget (₹/Acre)", 2000 if is_small_farmer else 5000, 10000 if is_small_farmer else 50000, 5000)
        
        if st.button("🚀 GET RECOMMENDATIONS"):
            recs = recommend_crops(df, le, soil, budget)
            if is_small_farmer: recs = recs[recs['Cost per Acre'] <= 10000].sort_values(by='Cost per Acre')
            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'<div class="main-card"><b>🌱 {row["Crop Name"]}</b><br>Cost: ₹{row["Cost per Acre"]}</div>', unsafe_allow_html=True)
            else: st.warning("No matches found. Try adjusting your budget.")

    # --- TAB 3: RENTAL HUB ---
    elif tab == "🚜 Rental Hub":
        st.header("🚜 Machinery & Support")
        with st.container(border=True):
            st.subheader("🛠️ Equipment Rental")
            st.link_button(f"Find Machinery in {s_dist}", f"https://www.google.com/search?q=tractor+rental+service+in+{s_dist}")
            st.markdown('<a href="tel:18001801551" class="call-btn">📞 Govt Helpline (1800-180-1551)</a>', unsafe_allow_html=True)

    # --- TAB 4: GOVT SCHEMES ---
    elif tab == "🏛️ Govt Schemes":
        st.header(f"🏛️ Schemes for {s_state}")
        t_state, t_center = st.tabs(["📍 State Level", "🇮🇳 Central Level"])
        with t_state:
            for s in get_state_schemes(s_state):
                with st.expander(f"🔹 {s['name']}"): st.write(s['details'])
        with t_center:
            for c in get_central_schemes():
                with st.expander(f"🔸 {c['name']}"): st.write(c['details'])

    # --- TAB 5: MARKET TRENDS ---
    elif tab == "📈 Market Trends":
        st.title("📈 Market Price Analysis")
        crop_list = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        c_name = st.selectbox("Choose Commodity", crop_list)
        live_data = get_live_mandi_prices(s_state, c_name)
        
        if live_data is not None:
            latest = live_data.iloc[0]
            st.metric(f"Price in {latest['market']}", f"₹{latest['modal_price']} / Qtl")
            live_data['modal_price'] = pd.to_numeric(live_data['modal_price'])
            st.plotly_chart(px.bar(live_data, x='market', y='modal_price', color_discrete_sequence=['#2e7d32']), use_container_width=True)
        
        st.divider()
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        prices = [1900, 1850, 2000, 2100, 2150, 2050, 2100, 2250, 2180, 2300, 2450, 2400]
        st.plotly_chart(px.line(x=months, y=prices, title=f"Annual Trend: {c_name}"), use_container_width=True)

    # --- TAB 6: AGRI LEDGER (WITH REPORT DOWNLOAD) ---
    elif tab == "📒 Agri Ledger":
        st.title("📒 Digital Agri Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT date, type, item, total, season FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income', na=False)]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense', na=False)]['total'].sum()
            
            m1, m2 = st.columns(2)
            m1.metric("Net Profit", f"₹{inc - exp:,.2f}")
            
            # REPORT DOWNLOAD FEATURE
            csv = df_khata.to_csv(index=False).encode('utf-8')
            m2.download_button("📥 Download Financial Report", data=csv, file_name=f"Agri_Report_{st.session_state.username}.csv", mime='text/csv')
            
            st.dataframe(df_khata, use_container_width=True, hide_index=True)
            if st.button("🗑️ Reset Ledger Data", type="primary"):
                delete_user_data(st.session_state.username)
                st.rerun()

        with st.expander("➕ Log New Transaction"):
            with st.form("ledger_form"):
                tp = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds)", "Expense (Labor)", "Expense (Machinery)"])
                itm = st.text_input("Item Name")
                val = st.number_input("Amount (₹)", min_value=0.0)
                sn = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"])
                if st.form_submit_button("Save Entry"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), tp, itm, "1", val, sn))
                    conn.commit()
                    conn.close()
                    st.rerun()
