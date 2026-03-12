import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="centered", page_icon="🌾")

# API Keys (Note: Use st.secrets for production deployment)
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070" 
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY", "YOUR_OPENWEATHER_KEY")

# --- HELPER FUNCTIONS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        data = requests.get(url).json()
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "desc": data["weather"][0]["description"].title(),
        }
    except:
        return None

# --- 2. MODULAR IMPORTS & FALLBACKS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
except ImportError:
    india_map = {"Bihar": ["Patna", "Gaya", "Muzaffarpur"]}
    all_crops = []
    def get_state_schemes(state): return []
    def get_central_schemes(): return []

# --- 3. DATABASE INITIALIZATION ---
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

# --- 4. CSS STYLING (Professional UI) ---
st.markdown("""
<style>
    .stApp { max-width: 850px; margin: 0 auto; }
    .mobile-card { 
        padding: 15px; border-radius: 12px; 
        border: 1px solid rgba(46, 125, 50, 0.3); 
        background-color: rgba(46, 125, 50, 0.05);
        margin-bottom: 12px;
    }
    .weather-card {
        background-color: #e3f2fd; padding: 20px; border-radius: 15px; 
        border-left: 10px solid #2196f3; margin-bottom: 20px;
    }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; width: 100%; }
    .call-btn { 
        background-color: #ffc107 !important; color: black !important; 
        padding: 12px; border-radius: 10px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 Agri-Smart Ecosystem")
    t_log, t_sign = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t_log:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Invalid credentials")
            conn.close()
    with t_sign:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                conn.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Account created! Go to Login.")
                conn.close()
            except: st.error("Username already taken.")

# --- 6. MAIN APP INTERFACE ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=90)
        st.subheader(f"User: {st.session_state.username}")
        menu = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🎯 AgriAI Engine", "🚜 Rental Hub", "🏛️ Govt Schemes", "📚 Knowledge Hub", "📉 Price Trends", "📒 Agri Ledger"])
        
        state_list = sorted(list(india_map.keys()))
        st_sel = st.selectbox("Your State", state_list)
        dt_sel = st.selectbox("Your District", sorted(india_map.get(st_sel, ["Patna"])))
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD: WEATHER & SMART ALERTS ---
    if menu == "🏠 Dashboard":
        weather = get_weather(dt_sel)
        if weather:
            st.markdown(f"""
            <div class="weather-card">
                <h3 style="margin:0; color: #0d47a1;">☁️ Live Weather: {dt_sel}</h3>
                <p style="margin:0; font-size: 26px;"><b>{weather['temp']}°C</b> | {weather['desc']}</p>
                <p style="margin:0; opacity: 0.8;">Humidity: {weather['humidity']}%</p>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("⚠️ Smart Agriculture Alerts")
            if weather['temp'] > 35:
                st.error(f"🔥 **High Heat Alert:** Temps in {dt_sel} are above 35°C. Increase irrigation.")
            elif weather['humidity'] > 80:
                st.warning(f"🪳 **Pest Risk:** High humidity detected. Monitor for fungal growth.")
            elif 20 <= weather['temp'] <= 30:
                st.success(f"✅ **Optimal Conditions:** Weather is ideal for most {st_sel} crops.")
            else:
                st.info("🚜 **Standard Advisory:** No extreme weather risks detected.")
        
        st.divider()
        st.subheader("📊 Ecosystem Overview")
        c1, c2, c3 = st.columns(3)
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT total, type FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()
        
        total_exp = df_khata[df_khata['type'].str.contains('Expense', na=False)]['total'].sum()
        c1.metric("System Status", "Live", delta="Sync Active")
        c2.metric("Total Ledger Exp", f"₹{total_exp:,.0f}")
        c3.metric("Project", "ASES-IITP", delta="v1.4")

    # --- AGRIAI ENGINE: KNN RECOMMENDATIONS + SMALL FARMER FILTER ---
    elif menu == "🎯 AgriAI Engine":
        st.header("🎯 Crop Recommendation Engine")
        df, le = get_agri_dataframe()
        
        is_small_farmer = st.sidebar.checkbox("🚜 Small Farmer Mode", help="Filters for low-investment, high-resilience crops.")
        soil = st.selectbox("Select Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy", "Loamy", "Heavy Soil"])
        
        if is_small_farmer:
            budget = st.slider("Investment Budget (₹/Acre)", 2000, 10000, 5000)
            st.caption("✨ Small Farmer Mode: Budget capped at ₹10,000.")
        else:
            budget = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
        
        if st.button("🚀 GET RECOMMENDATIONS"):
            recs = recommend_crops(df, le, soil, budget)
            if is_small_farmer:
                recs = recs[recs['Cost per Acre'] <= 10000].sort_values(by='Cost per Acre')

            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'''<div class="mobile-card">
                        <b>🌱 {row["Crop Name"]}</b><br>
                        <small>Cost: ₹{row["Cost per Acre"]}/Acre | Sowing: Month {int(row["Sowing Month"])}</small>
                    </div>''', unsafe_allow_html=True)
            else: st.warning("No matches found. Try adjusting the budget.")

    # --- RENTAL HUB: HELPLINE & GEO-LINKS ---
    elif menu == "🚜 Rental Hub":
        st.header("🚜 Machinery Rentals")
        cat = st.segmented_control("Category", ["Preparation", "Sowing", "Harvesting"], default="Preparation")
        machines = {"Preparation": [("Rotavator", "🚜")], "Sowing": [("Seed Drill", "🌱")], "Harvesting": [("Thresher", "🌪️")]}
        
        for name, icon in machines.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Find in {dt_sel}", f"https://www.google.com/search?q={name}+rental+service+in+{dt_sel}")
                st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Call Govt Helpline (1800-180-1551)</a>', unsafe_allow_html=True)

    # --- GOVT SCHEMES: STATE & CENTRAL ---
    elif menu == "🏛️ Govt Schemes":
        st.header(f"🏛️ Agriculture Schemes: {st_sel}")
        t1, t2 = st.tabs(["📍 State Schemes", "🇮🇳 Central Schemes"])
        with t1:
            s_schemes = get_state_schemes(st_sel)
            if s_schemes:
                for s in s_schemes:
                    with st.expander(f"🔹 {s['name']}"): st.write(s['details'])
            else: st.info("Loading latest state-specific initiatives...")
        with t2:
            c_schemes = get_central_schemes()
            for cs in c_schemes:
                with st.expander(f"🔸 {cs['name']}"): st.write(cs['details'])

    # --- KNOWLEDGE HUB: CROP LIBRARY ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Detailed Crop Library")
        q = st.text_input("🔍 Search Crop...").strip()
        filtered = [c for c in all_crops if q.lower() in c['Crop'].lower()] if q else all_crops
        for item in filtered:
            with st.expander(f"📖 {item['Crop']} ({item['Type']})"):
                st.write(f"**Season:** {item['Season']} | **Soil:** {item['Soil']}")
                st.success(f"💡 **Expert Tip:** {item['Pro-Tip']}")

    # --- PRICE TRENDS: LIVE OGD API ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        c_names = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        sel_c = st.selectbox("Choose Commodity", c_names)
        
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": st_sel, "filters[commodity]": sel_c}
        try:
            res = requests.get(f"https://api.data.gov.in/resource/{RESOURCE_ID}", params=params).json()
            if "records" in res and res["records"]:
                latest = res["records"][0]
                st.metric(f"Mandi Price ({latest['market']})", f"₹{latest['modal_price']} / Quintal")
                mandi_df = pd.DataFrame(res["records"])
                st.plotly_chart(px.bar(mandi_df, x='market', y='modal_price', color_discrete_sequence=['#2e7d32']), use_container_width=True)
            else: st.warning("Live data currently unavailable for this selection.")
        except: st.error("Mandi Server Connection Failed.")

    # --- AGRI LEDGER: SQL STORAGE & EXPORT ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Digital Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT date, type, item, total FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income', na=False)]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense', na=False)]['total'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("Net Savings", f"₹{inc - exp:,.2f}")
            csv = df_khata.to_csv(index=False).encode('utf-8')
            col2.download_button("📥 Download Report (CSV)", data=csv, file_name=f"Report_{st.session_state.username}.csv", mime='text/csv')
            
            st.divider()
            st.dataframe(df_khata, use_container_width=True, hide_index=True)
        
        with st.expander("➕ Add Transaction"):
            with st.form("ledger_form"):
                t_type = st.selectbox("Type", ["Expense (Seeds)", "Expense (Labor)", "Income (Sales)"])
                t_item = st.text_input("Description")
                t_amt = st.number_input("Amount (₹)", min_value=0.0)
                if st.form_submit_button("Save Entry"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, total) VALUES (?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t_type, t_item, t_amt))
                    conn.commit()
                    conn.close()
                    st.rerun()
