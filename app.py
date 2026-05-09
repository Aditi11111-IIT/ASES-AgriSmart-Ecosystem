import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
import os
from datetime import datetime

# --- 1. CONFIGURATION & API ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="centered", page_icon="🌾")
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# --- 2. MOCK DATA GENERATION (Machinery Owners) ---
def init_machinery_csv():
    if not os.path.exists('machinery.csv'):
        data = {
            "Owner": ["Rajesh Kumar", "Amit Singh", "Suresh Mehra", "Vikram Jeet", "Priyanka Devi", "Sunil Verma"],
            "Phone": ["9876543210", "9123456789", "9988776655", "9412345678", "8877665544", "7766554433"],
            "Machine": ["Rotavator", "Seed Drill", "Harvester", "Power Tiller", "Transplanter", "Thresher"],
            "District": ["Patna", "Gaya", "Patna", "Gaya", "Patna", "Gaya"],
            "Rate": ["₹800/hr", "₹500/hr", "₹2500/hr", "₹400/hr", "₹1200/hr", "₹1000/hr"]
        }
        pd.DataFrame(data).to_csv('machinery.csv', index=False)

init_machinery_csv()

# --- 3. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
except ImportError:
    india_map = {"Bihar": ["Patna", "Gaya"]}
    all_crops = []

# --- 4. DATABASE (SECURE PER-USER) ---
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

# --- 5. MOBILE-FRIENDLY CSS ---
st.markdown("""
<style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .mobile-card { 
        padding: 15px; border-radius: 12px; 
        border: 1px solid rgba(46, 125, 50, 0.3); 
        background-color: rgba(46, 125, 50, 0.05);
        margin-bottom: 10px;
    }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; }
    .call-btn { 
        background-color: #ffc107 !important; color: black !important; 
        padding: 12px; border-radius: 10px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
    .badge {
        background: #2e7d32; color: white; padding: 2px 8px; 
        border-radius: 8px; font-size: 0.8em; float: right;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. AUTHENTICATION ---
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

# --- 7. MAIN APP ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=80)
        st.write(f"🧑‍🌾 **{st.session_state.username}**")
        
        menu = st.radio("Go to", ["🏠 Dashboard", "🎯 AgriAI Engine", "🏛️ Govt Schemes", "🚜 Rental Hub", "📚 Knowledge Hub", "📉 Price Trends", "📒 Agri Ledger"])
        
        state_sel = st.selectbox("State", sorted(india_map.keys()))
        dist_sel = st.selectbox("District", sorted(india_map.get(state_sel, ["Patna"])))
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD ---
      # --- DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.header(f"Welcome to {dist_sel}")

        WEATHER_API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"
        # Current weather
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={dist_sel},{state_sel},IN&appid={WEATHER_API_KEY}&units=metric"

        try:
            w_data = requests.get(weather_url).json()
            if w_data.get("main"):
                temp = w_data["main"]["temp"]
                cond = w_data["weather"][0]["description"].title()
                hum = w_data["main"]["humidity"]

                c1, c2, c3 = st.columns(3)
                c1.metric("🌡️ Temp", f"{temp}°C")
                c2.metric("☁️ Condition", cond)
                c3.metric("💧 Humidity", f"{hum}%")

                # --- 7-Day Forecast ---
                lat, lon = w_data["coord"]["lat"], w_data["coord"]["lon"]
                forecast_url = f"http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={WEATHER_API_KEY}&units=metric"
                f_data = requests.get(forecast_url).json()

                if "daily" in f_data:
                    days = []
                    temps = []
                    for d in f_data["daily"][:7]:
                        day = datetime.fromtimestamp(d["dt"]).strftime("%a")
                        days.append(day)
                        temps.append(d["temp"]["day"])
                    st.plotly_chart(px.line(x=days, y=temps, markers=True,
                                            title="🌤️ 7-Day Temperature Forecast"),
                                    use_container_width=True)
                else:
                    st.info("Forecast data not available.")
            else:
                st.warning("⚠️ Weather data not available for this location.")
        except Exception as e:
            st.error("Weather API connection failed.")

        st.info("💡 Check Market Trends for live prices from government mandis.")


    # --- AGRIAI ENGINE ---
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
            else: st.warning("Try a higher budget.")

    # --- GOVT SCHEMES SECTION ---
    elif menu == "🏛️ Govt Schemes":
        st.header(f"🏛️ Schemes for {state_sel}")
        state_data = get_state_schemes()
        current_scheme = state_data.get(state_sel)

        if current_scheme:
            st.subheader(f"📍 State Special: {state_sel}")
            with st.container(border=True):
                st.markdown(f"### {current_scheme['name']}")
                st.write(current_scheme['desc'])
                st.link_button(f"Apply on {state_sel} Portal", current_scheme['link'])
        else:
            st.info(f"Looking for specific {state_sel} schemes... Check the Central list below.")

        st.divider()
        st.subheader("🌍 Central Government Schemes")
        central_schemes = get_central_schemes()
        
        for scheme in central_schemes:
            with st.expander(f"✨ {scheme['name']}"):
                st.write(scheme['desc'])
                st.link_button("View Official Website", scheme['link'])

        st.info("💡 Tip: Keep your Aadhaar and Land Records ready for application.")

    # --- RENTAL HUB (UPDATED WITH MACHINERY.CSV) ---
       # --- RENTAL HUB ---
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
                st.link_button(f"Find in {dist_sel}", f"https://www.google.com/search?q={m_name}+rental+in+{dist_sel}")
                st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Govt Help</a>', unsafe_allow_html=True)

        # --- MOCK DATABASE OF MACHINERY OWNERS ---
        st.divider()
        st.subheader("📋 Local Machinery Owners")

        # Load mock CSV (machinery.csv)
        try:
            owners_df = pd.read_csv("machinery.csv")
            search_q = st.text_input("🔍 Search Owner / Shop")
            if search_q:
                owners_df = owners_df[owners_df.apply(lambda row: search_q.lower() in str(row).lower(), axis=1)]
            st.dataframe(owners_df, use_container_width=True)

            # Click-to-call buttons
            for _, row in owners_df.iterrows():
                st.markdown(f'''
                    <div class="mobile-card">
                        <b>{row["Owner"]}</b> — {row["Machine"]}
                        <br>📍 {row["Location"]}
                        <a href="tel:{row["Phone"]}" class="call-btn">📞 Call {row["Owner"]}</a>
                        <a href="https://www.google.com/search?q={row["Owner"]}+{row["Location"]}+rental" class="call-btn">🔍 Search Shop</a>
                    </div>
                ''', unsafe_allow_html=True)
        except Exception as e:
            st.warning("⚠️ Machinery database not found. Please ensure 'machinery.csv' exists.")


    # --- KNOWLEDGE HUB ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Crop Library")
        with st.expander("⚖️ Compare Two Crops"):
            c_names = [c['Crop'] for c in all_crops]
            ca, cb = st.columns(2)
            crop_1 = ca.selectbox("Crop 1", c_names, index=0)
            crop_2 = cb.selectbox("Crop 2", c_names, index=1)
            
            d1 = next(i for i in all_crops if i["Crop"] == crop_1)
            d2 = next(i for i in all_crops if i["Crop"] == crop_2)
            
            comp_df = pd.DataFrame({
                "Feature": ["Type", "Soil", "Season", "Water"],
                crop_1: [d1['Type'], d1['Soil'], d1['Season'], d1['Water']],
                crop_2: [d2['Type'], d2['Soil'], d2['Season'], d2['Water']]
            })
            st.table(comp_df.set_index("Feature"))

        st.divider()
        q = st.text_input("🔍 Search Crop (e.g., Wheat, Sandy, Fruit)")
        filtered = [c for c in all_crops if q.lower() in str(c).lower()] if q else all_crops
        
        for item in filtered:
            st.markdown(f'''
                <div class="mobile-card">
                    <span class="badge">{item['Type']}</span>
                    <b>🌱 {item['Crop']}</b><br>
                    <small>📍 {item['Season']} | ⏳ {item['Harvesting']}</small>
                </div>
            ''', unsafe_allow_html=True)
            with st.expander("🔍 View Details & Pro-Tip"):
                c1, c2 = st.columns(2)
                c1.write(f"🧪 **NPK:** {item['N-P-K']}")
                c1.write(f"🌍 **Soil:** {item['Soil']}")
                c2.write(f"💧 **Water:** {item['Water']}")
                c2.write(f"🐛 **Pest:** {item['Pest']}")
                st.info(f"💡 **Tip:** {item['Pro-Tip']}")

    # --- PRICE TRENDS ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        c_list = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        sel_c = st.selectbox("Commodity", c_list)
        
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        p = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": state_sel, "filters[commodity]": sel_c}
        
        try:
            data = requests.get(url, params=p).json()
            if "records" in data and data["records"]:
                latest = data["records"][0]
                st.metric(f"Live Price in {latest['market']}", f"₹{latest['modal_price']}")
            else: st.info("No live data for today. Showing historical trend.")
        except: st.error("API connection failed.")
        
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        vals = [2100, 2050, 2150, 2200, 2300, 2250, 2350, 2400, 2380, 2450, 2500, 2480]
        st.plotly_chart(px.line(x=months, y=vals, title="Annual Price Cycle"), use_container_width=True)

    # --- AGRI LEDGER ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            st.subheader(f"Balance: ₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True)
        
        with st.expander("➕ Add Entry"):
            with st.form("add_f"):
                t = st.selectbox("Type", ["Income (Sales)", "Expense (Seeds/Labor)"])
                itm = st.text_input("Item")
                amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Save Entry"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t, itm, "1", amt, "General"))
                    conn.commit()
                    conn.close()
                    st.rerun()
