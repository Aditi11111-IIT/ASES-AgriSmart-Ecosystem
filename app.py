import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="centered", page_icon="🌾")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070" 
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY", "YOUR_OPENWEATHER_KEY") # Ensure this is in your secrets

# --- NEW: WEATHER API HELPER ---
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

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
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

# --- 4. CSS STYLING ---
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

# --- 5. AUTHENTICATION ---
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
        menu = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🎯 AgriAI Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "📉 Price Trends", "📒 Agri Ledger"])
        
        state_list = sorted(list(india_map.keys()))
        st_sel = st.selectbox("Your State", state_list)
        dt_sel = st.selectbox("Your District", sorted(india_map.get(st_sel, ["Patna"])))
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD (DYNAMIC & PROFESSIONAL) ---
    if menu == "🏠 Dashboard":
        # 1. Fetch live weather
        weather = get_weather(dt_sel)
        
        # 2. Display Weather Header
        if weather:
            st.markdown(f"""
            <div class="weather-card">
                <h3 style="margin:0; color: #0d47a1;">☁️ Live Weather: {dt_sel}</h3>
                <p style="margin:0; font-size: 26px;"><b>{weather['temp']}°C</b> | {weather['desc']}</p>
                <p style="margin:0; opacity: 0.8;">Humidity: {weather['humidity']}%</p>
            </div>
            """, unsafe_allow_html=True)

            # 3. Dynamic Farmer Alerts (Logic-Based)
            st.subheader("⚠️ Smart Agriculture Alerts")
            
            if weather['temp'] > 35:
                st.error(f"🔥 **High Heat Alert:** Temperatures in {dt_sel} are above 35°C. Increase irrigation frequency to prevent crop wilting.")
            elif weather['humidity'] > 80:
                st.warning(f"🪳 **Pest Risk:** High humidity ({weather['humidity']}%) detected. Monitor for fungal growth or aphid infestations.")
            elif 20 <= weather['temp'] <= 30:
                st.success(f"✅ **Optimal Conditions:** Weather in {dt_sel} is ideal for most {st_sel} crops. Proceed with planned fertilization.")
            else:
                st.info("🚜 **Standard Advisory:** No extreme weather risks detected for the next 6 hours.")
        
        st.divider()

        # 4. Professional Metrics
        st.subheader("📊 Ecosystem Overview")
        c1, c2, c3 = st.columns(3)
        
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()
        
        total_exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
        
        c1.metric("System", "Sync Active", delta="Live")
        c2.metric("Total Investment", f"₹{total_exp:,.0f}", delta=f"{len(df_khata)} Entries")
        c3.metric("Project ID", "ASES-IITP", delta="v1.4-Dev")

        st.info("💡 **Pro-Tip:** Check the 'Price Trends' tab before selling your harvest to find the best Mandi rates.")

    # --- AGRIAI ENGINE (WITH SMALL FARMER FILTER) ---
    elif menu == "🎯 AgriAI Engine":
        st.header("🎯 Crop Recommendation Engine")
        df, le = get_agri_dataframe()
        
        # --- NEW: SMALL FARMER FILTER ---
        st.sidebar.markdown("---")
        is_small_farmer = st.sidebar.checkbox("🚜 Small Farmer Mode", help="Filters for low-investment, high-resilience crops.")
        
        soil = st.selectbox("Select Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy", "Loamy", "Heavy Soil"])
        
        if is_small_farmer:
            budget = st.slider("Investment Budget (₹/Acre)", 2000, 10000, 5000)
            st.caption("✨ Small Farmer Mode Active: Budget capped at ₹10,000 for low-risk farming.")
        else:
            budget = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
        
        if st.button("🚀 GET RECOMMENDATIONS"):
            recs = recommend_crops(df, le, soil, budget)
            
            # Apply additional filtering logic for Small Farmers if checked
            if is_small_farmer:
                # Assuming 'Cost per Acre' is a column in your DataFrame
                recs = recs[recs['Cost per Acre'] <= 10000].sort_values(by='Cost per Acre')

            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'''<div class="mobile-card">
                        <b>🌱 {row["Crop Name"]}</b><br>
                        <small>Estimated Cost: ₹{row["Cost per Acre"]}/Acre</small><br>
                        <small>Recommended Sowing: Month {int(row["Sowing Month"])}</small>
                    </div>''', unsafe_allow_html=True)
            else: st.warning("No matches. Try adjusting your budget.")

    # --- RENTAL HUB ---
    elif menu == "🚜 Rental Hub":
        st.header("🚜 Machinery Rentals")
        cat = st.segmented_control("Service Category", ["Preparation", "Sowing", "Harvesting"], default="Preparation")
        machines = {
            "Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
            "Sowing": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
            "Harvesting": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
        }
        for name, icon in machines.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Find in {dt_sel}", f"https://www.google.com/search?q={name}+rental+service+in+{dt_sel}")
                st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Call Govt Helpline</a>', unsafe_allow_html=True)

    # --- KNOWLEDGE HUB ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Detailed Crop Library")
        q = st.text_input("🔍 Search Crop (e.g., Wheat, Mustard)...").strip()
        filtered = [c for c in all_crops if q.lower() in c['Crop'].lower()] if q else all_crops
        
        for item in filtered:
            with st.expander(f"📖 {item['Crop']} ({item['Type']})"):
                c_a, c_b = st.columns(2)
                c_a.write(f"**Season:** {item['Season']}")
                c_a.write(f"**Soil:** {item['Soil']}")
                c_b.write(f"**N-P-K:** {item['N-P-K']}")
                c_b.write(f"**Water:** {item['Water']}")
                st.success(f"💡 **Expert Tip:** {item['Pro-Tip']}")

    # --- PRICE TRENDS ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        c_names = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        sel_c = st.selectbox("Choose Commodity", c_names)
        
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": st_sel, "filters[commodity]": sel_c}
        
        try:
            res = requests.get(url, params=params).json()
            if "records" in res and res["records"]:
                latest = res["records"][0]
                st.success(f"Latest Data for {sel_c} in {st_sel}")
                st.metric(f"Mandi Price ({latest['market']})", f"₹{latest['modal_price']} / Quintal")
                
                mandi_df = pd.DataFrame(res["records"])
                mandi_df['modal_price'] = pd.to_numeric(mandi_df['modal_price'])
                st.plotly_chart(px.bar(mandi_df, x='market', y='modal_price', title="Price across local Mandis", color_discrete_sequence=['#2e7d32']), use_container_width=True)
            else:
                st.warning(f"Live data for {sel_c} in {st_sel} is currently unavailable. Showing historical trend.")
        except:
            st.error("Could not connect to live Mandi servers.")

        st.divider()
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        vals = [2100, 2050, 2150, 2200, 2300, 2250, 2350, 2400, 2380, 2450, 2500, 2480]
        st.plotly_chart(px.line(x=months, y=vals, title=f"Annual Price Cycle: {sel_c}", markers=True), use_container_width=True)

    # --- AGRI LEDGER ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Digital Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            st.subheader(f"Current Profit: ₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        else:
            st.info("No personal records found.")

        with st.expander("➕ Add Transaction"):
            with st.form("new_entry"):
                t_type = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds/Labor)", "Expense (Machinery)"])
                t_item = st.text_input("Description (e.g., Urea, Wheat Sale)")
                t_amt = st.number_input("Amount (₹)", min_value=0.0)
                if st.form_submit_button("Save to Ledger"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t_type, t_item, "1", t_amt, "Current"))
                    conn.commit()
                    conn.close()
                    st.rerun()
