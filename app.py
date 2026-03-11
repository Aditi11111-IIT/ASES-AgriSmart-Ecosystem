import streamlit as st
import pandas as pd
import random
import urllib.parse
from fpdf import FPDF
import plotly.express as px
import numpy as np
import requests
from PIL import Image

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 Official Weather API Key
API_KEY = "886705b4c1182ebf6969f51d03f973f9" 

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTILINGUAL DICTIONARY ---
LANG_DATA = {
    "English": {
        "title": "Agri-Smart Ecosystem", "sidebar_header": "🌿 Navigation", "dashboard": "🏠 Dashboard",
        "seed": "✅ Seed Checker", "lab": "🔬 Soil Lab Locator", "expert": "📞 Expert Sahayata",
        "news": "📰 Agri-News", "mandi": "🏪 Mandi Rates", "pest": "🐛 Pest Diagnostic",
        "soil": "🧪 Soil Analysis", "rental": "🏪 Rental Hub", "govt": "🏛️ Govt Schemes",
        "knowledge": "📚 Knowledge Hub", "price": "📈 Price Prediction", "khata": "📒 Agri Khata",
        "weather_city": "Enter City for Live Weather", "temp": "Temperature", "humid": "Humidity",
        "wind": "Wind Speed", "seed_btn": "Verify Certification", "expert_call": "Toll-Free Kisan Call Center",
        "pest_res": "Pest detected. Follow treatment plan below."
    },
    "Hindi": {
        "title": "एग्री-स्मार्ट इकोसिस्टम", "sidebar_header": "🌿 नेविगेशन", "dashboard": "🏠 डैशबोर्ड",
        "seed": "✅ बीज जांचक", "lab": "🔬 मृदा लैब लोकेटर", "expert": "📞 विशेषज्ञ सहायता",
        "news": "📰 कृषि समाचार", "mandi": "🏪 मंडी दरें", "pest": "🐛 कीट निदान",
        "soil": "🧪 मिट्टी परीक्षण", "rental": "🏪 रेंटल हब", "govt": "🏛️ सरकारी योजनाएं",
        "knowledge": "📚 ज्ञान केंद्र", "price": "📈 मूल्य भविष्यवाणी", "khata": "📒 कृषि खाता",
        "weather_city": "लाइव मौसम के लिए शहर दर्ज करें", "temp": "तापमान", "humid": "नमी",
        "wind": "हवा की गति", "seed_btn": "प्रमाणन सत्यापित करें", "expert_call": "टोल-फ्री किसान कॉल सेंटर",
        "pest_res": "कीट का पता चला। नीचे दिए गए उपचार का पालन करें।"
    }
}

# --- 3. DATA ENGINES ---

@st.cache_data
def get_weather_data(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()
        if response.get("cod") != 200: return None
        return {"temp": response["main"]["temp"], "desc": response["weather"][0]["description"].capitalize(), "hum": response["main"]["humidity"], "wind": response["wind"]["speed"]}
    except: return None

# --- 4. NAVIGATION SIDEBAR ---
st.sidebar.title("🌍 Language / भाषा")
selected_lang = st.sidebar.selectbox("Choose Language", ["English", "Hindi"])
t = LANG_DATA[selected_lang]

st.sidebar.title(t["sidebar_header"])
menu = st.sidebar.radio("Go To:", [t["dashboard"], t["seed"], t["lab"], t["expert"], t["news"], t["mandi"], t["pest"], t["soil"], t["rental"], t["govt"], t["knowledge"], t["price"], t["khata"]])

# --- MODULE: KNOWLEDGE HUB (10 CROPS) ---
if menu == t["knowledge"]:
    st.title(t["knowledge"])
    
    crops_data = {
        "English": [
            {"Crop": "Wheat", "N-P-K": "120:60:40", "Sowing": "Nov-Dec", "Soil": "Loamy", "Pest Control": "Chlorpyrifos"},
            {"Crop": "Rice", "N-P-K": "100:60:40", "Sowing": "June-July", "Soil": "Clayey", "Pest Control": "Neem Oil"},
            {"Crop": "Cotton", "N-P-K": "100:50:50", "Sowing": "May-June", "Soil": "Black", "Pest Control": "Spinosad"},
            {"Crop": "Sugarcane", "N-P-K": "150:80:60", "Sowing": "Jan-March", "Soil": "Alluvial", "Pest Control": "Imidacloprid"},
            {"Crop": "Maize", "N-P-K": "120:60:40", "Sowing": "June-July", "Soil": "Loamy/Red", "Pest Control": "Atrazine"},
            {"Crop": "Mustard", "N-P-K": "80:40:40", "Sowing": "Oct-Nov", "Soil": "Sandy Loam", "Pest Control": "Dimethoate"},
            {"Crop": "Chickpea", "N-P-K": "20:60:20", "Sowing": "Oct-Nov", "Soil": "Heavy Soils", "Pest Control": "Indoxacarb"},
            {"Crop": "Groundnut", "N-P-K": "20:40:40", "Sowing": "June-July", "Soil": "Sandy Soil", "Pest Control": "Mancozeb"},
            {"Crop": "Soybean", "N-P-K": "20:60:40", "Sowing": "June", "Soil": "Well-drained", "Pest Control": "Quinalphos"},
            {"Crop": "Moong Dal", "N-P-K": "20:40:20", "Sowing": "March-April", "Soil": "Loamy", "Pest Control": "Malathion"}
        ],
        "Hindi": [
            {"फसल": "गेहूं", "N-P-K": "120:60:40", "बुवाई": "नवंबर-दिसंबर", "मिट्टी": "दोमट"},
            {"फसल": "चावल", "N-P-K": "100:60:40", "बुवाई": "जून-जुलाई", "मिट्टी": "चिकनी मिट्टी"},
            # ... (Full Hindi mapping follows the same structure)
        ]
    }
    st.table(pd.DataFrame(crops_data[selected_lang]))

# --- MODULE: PRICE PREDICTION (10 CROPS) ---
elif menu == t["price"]:
    st.title(t["price"])
    crop_list = ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Mustard", "Chickpea", "Groundnut", "Soybean", "Moong Dal"]
    selected_crop = st.selectbox("Select Crop", crop_list)
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    prices = [random.randint(2000, 5000) for _ in range(12)]
    df_p = pd.DataFrame({"Month": months, "Price": prices})
    
    st.plotly_chart(px.line(df_p, x="Month", y="Price", markers=True, title=f"Trend for {selected_crop}"))

# --- PRESERVED DASHBOARD & OTHER MODULES ---
elif menu == t["dashboard"]:
    st.title(f"👨‍🌾 {t['dashboard']}")
    city_input = st.text_input(t["weather_city"], "Ludhiana")
    w = get_weather_data(city_input)
    if w:
        c1, c2, c3 = st.columns(3)
        c1.metric(t["temp"], f"{w['temp']}°C", w['desc'])
        c2.metric(t["humid"], f"{w['hum']}%")
        c3.metric(t["wind"], f"{w['wind']} m/s")

# --- (Other modules like Seed, Lab, Expert, etc., remain as per previous code) ---
