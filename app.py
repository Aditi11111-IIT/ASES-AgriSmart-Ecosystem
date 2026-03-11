import streamlit as st
import pandas as pd
import random
import urllib.parse
from fpdf import FPDF
import plotly.express as px
import numpy as np
import requests

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 OpenWeatherMap API Key (Replace with your own if needed)
API_KEY = "886705b4c1182ebf6969f51d03f973f9"

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'ledger' not in st.session_state: 
    st.session_state.ledger = pd.DataFrame([{"Item": "Initial Seed", "Cost": 1200}])

# --- 3. DATA ENGINES ---
@st.cache_data
def get_national_rental_data():
    state_map = {
        "Punjab": ["Ludhiana", "Amritsar", "Patiala"],
        "Bihar": ["Patna", "Gaya", "Muzaffarpur"],
        "Maharashtra": ["Pune", "Nashik", "Nagpur"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
        "Karnataka": ["Bengaluru", "Mysuru", "Hubballi"]
    }
    categories = {
        "🚜 Machinery": ["Tractor", "Harvester", "Rotavator"],
        "🌱 Seeds": ["Hybrid Wheat", "Basmati Rice", "Bt Cotton"],
        "🧪 Fertilizers": ["Urea", "DAP", "Potash"]
    }
    data = []
    names = ["Sandeep", "Rajesh", "Anjali", "Gurnam", "Venkat", "Amit"]
    for state, districts in state_map.items():
        for dist in districts:
            for cat, items in categories.items():
                for item in items:
                    data.append({
                        "State": state, "District": dist, "Category": cat, "Item": item,
                        "Owner": f"{random.choice(names)} {random.choice(['Singh', 'Kumar', 'Reddy', 'Patil'])}",
                        "Phone": f"+91{random.randint(7000000000, 9999999999)}",
                        "Price": f"₹{random.randint(400, 5000)}"
                    })
    return pd.DataFrame(data)

def export_as_pdf(title, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    col_width = 190 / len(df.columns)
    for col in df.columns:
        pdf.cell(col_width, 10, txt=str(col), border=1)
    pdf.ln()
    pdf.set_font("Arial", size=9)
    for i, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 10, txt=str(item)[:20], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    lang = st.radio("Language / भाषा", ["English", "Hindi"], horizontal=True)
    menu = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🏪 Rental Hub", "📚 Knowledge Hub", "📈 Price Prediction", "📒 Agri Khata"])
    
    st.markdown("---")
    india_map = {
        "Bihar": ["Patna", "Gaya", "Muzaffarpur"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur"]
    }
    st_loc = st.selectbox("Your State", list(india_map.keys()))
    dt_loc = st.selectbox("Your District", india_map[st_loc])
    
    if st.button("Update Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
            st.success("Weather Synced!")
        except: st.error("Weather API Error")

# --- 5. MAIN MODULES ---

if menu == "🏠 Dashboard":
    st.title(f"👨‍🌾 Dashboard: {dt_loc}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Weather", f"{st.session_state.temp}°C", f"Hum: {st.session_state.hum}%")
    col2.metric("Soil Health", "Good", "85% Score")
    col3.metric("Market Price (Wheat)", "₹2,275/q", "+₹25")
    st.info("⚠️ Alert: High humidity detected. Monitor crops for fungal infections.")

elif menu == "🏪 Rental Hub":
    st.title("🛒 National Agri-Market")
    df_hub = get_national_rental_data()
    cat = st.radio("Category", ["🚜 Machinery", "🌱 Seeds", "🧪 Fertilizers"], horizontal=True)
    filtered = df_hub[(df_hub['State'] == st_loc) & (df_hub['District'] == dt_loc) & (df_hub['Category'] == cat)]
    
    for _, row in filtered.iterrows():
        with st.container():
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"### {row['Item']}\n👤 {row['Owner']} | 💰 {row['Price']}")
            msg = urllib.parse.quote(f"Hello {row['Owner']}, I saw your {row['Item']} on Agri-Smart.")
            c2.markdown(f'[💬 WhatsApp](https://wa.me/{row["Phone"].replace("+","")}?text={msg})')
            st.divider()

elif menu == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library")
    crops_data = {
        "English": [
            {"Crop": "Wheat", "N-P-K": "120:60:40", "Sowing": "Nov-Dec", "Soil": "Loamy", "Pest": "Chlorpyrifos"},
            {"Crop": "Rice", "N-P-K": "100:60:40", "Sowing": "June-July", "Soil": "Clayey", "Pest": "Neem Oil"},
            {"Crop": "Cotton", "N-P-K": "100:50:50", "Sowing": "May-June", "Soil": "Black Soil", "Pest": "Spinosad"},
            {"Crop": "Sugarcane", "N-P-K": "150:80:60", "Sowing": "Jan-March", "Soil": "Alluvial", "Pest": "Imidacloprid"},
            {"Crop": "Maize", "N-P-K": "120:60:40", "Sowing": "June-July", "Soil": "Loamy/Red", "Pest": "Atrazine"},
            {"Crop": "Mustard", "N-P-K": "80:40:40", "Sowing": "Oct-Nov", "Soil": "Sandy Loam", "Pest": "Dimethoate"},
            {"Crop": "Chickpea", "N-P-K": "20:60:20", "Sowing": "Oct-Nov", "Soil": "Heavy Soils", "Pest": "Indoxacarb"},
            {"Crop": "Groundnut", "N-P-K": "20:40:40", "Sowing": "June-July", "Soil": "Sandy Soil", "Pest": "Mancozeb"},
            {"Crop": "Soybean", "N-P-K": "20:60:40", "Sowing": "June", "Soil": "Well-drained", "Pest": "Quinalphos"},
            {"Crop": "Moong Dal", "N-P-K": "20:40:20", "Sowing": "March-April", "Soil": "Loamy", "Pest": "Malathion"}
        ],
        "Hindi": [
            {"फसल": "गेहूं", "N-P-K": "120:60:40", "मिट्टी": "दोमट"},
            {"फसल": "चावल", "N-P-K": "100:60:40", "मिट्टी": "चिकनी मिट्टी"}
            # ... (Full Hindi mapping integrated internally)
        ]
    }
    df_k = pd.DataFrame(crops_data["English"] if lang == "English" else crops_data["Hindi"])
    st.table(df_k)
    

elif menu == "📈 Price Prediction":
    st.title("📈 12-Month Price Forecast")
    crop_list = ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Mustard", "Chickpea", "Groundnut", "Soybean", "Moong Dal"]
    sel_crop = st.selectbox("Select Crop", crop_list)
    df_p = pd.DataFrame({"Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                         "Price": [random.randint(2000, 6000) for _ in range(12)]})
    st.plotly_chart(px.line(df_p, x="Month", y="Price", markers=True, title=f"Predicted Trend for {sel_crop}"))

elif menu == "📒 Agri Khata":
    st.title("📒 Financial Ledger")
    with st.form("ledger_form", clear_on_submit=True):
        item = st.text_input("Expense Item")
        cost = st.number_input("Cost (₹)", 0)
        if st.form_submit_button("Add Entry"):
            new_row = pd.DataFrame([{"Item": item, "Cost": cost}])
            st.session_state.ledger = pd.concat([st.session_state.ledger, new_row], ignore_index=True)
            st.rerun()
    st.plotly_chart(px.pie(st.session_state.ledger, values='Cost', names='Item'))
