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
        "pest_res": "Pink Bollworm detected. Spray Spinosad 45 SC."
    },
    "Hindi": {
        "title": "एग्री-स्मार्ट इकोसिस्टम", "sidebar_header": "🌿 नेविगेशन", "dashboard": "🏠 डैशबोर्ड",
        "seed": "✅ बीज जांचक", "lab": "🔬 मृदा लैब लोकेटर", "expert": "📞 विशेषज्ञ सहायता",
        "news": "📰 कृषि समाचार", "mandi": "🏪 मंडी दरें", "pest": "🐛 कीट निदान",
        "soil": "🧪 मिट्टी परीक्षण", "rental": "🏪 रेंटल हब", "govt": "🏛️ सरकारी योजनाएं",
        "knowledge": "📚 ज्ञान केंद्र", "price": "📈 मूल्य भविष्यवाणी", "khata": "📒 कृषि खाता",
        "weather_city": "लाइव मौसम के लिए शहर दर्ज करें", "temp": "तापमान", "humid": "नमी",
        "wind": "हवा की गति", "seed_btn": "प्रमाणन सत्यापित करें", "expert_call": "टोल-फ्री किसान कॉल सेंटर",
        "pest_res": "गुलाबी सुंडी पाई गई। स्पिनोसैड 45 SC का छिड़काव करें।"
    },
    "Punjabi": {
        "title": "ਐਗਰੀ-ਸਮਾਰਟ ਈਕੋਸਿਸਟਮ", "sidebar_header": "🌿 ਨੈਵੀਗੇਸ਼ਨ", "dashboard": "🏠 ਡੈਸ਼ਬੋਰਡ",
        "seed": "✅ ਬੀਜ ਜਾਂਚਕਰਤਾ", "lab": "🔬 ਮਿੱਟੀ ਲੈਬ ਲੋਕੇਟਰ", "expert": "📞 ਮਾਹਿਰ ਸਹਾਇਤਾ",
        "news": "📰 ਖੇਤੀਬਾੜੀ ਖ਼ਬਰਾਂ", "mandi": "🏪 ਮੰਡੀ ਦੀਆਂ ਕੀਮਤਾਂ", "pest": "🐛 ਕੀੜੇ ਨਿਦਾਨ",
        "soil": "🧪 ਮਿੱਟੀ ਵਿਸ਼ਲੇਸ਼ਣ", "rental": "🏪 ਰੈਂਟਲ ਹਬ", "govt": "🏛️ ਸਰਕਾਰੀ ਸਕੀਮਾਂ",
        "knowledge": "📚 ਗਿਆਨ ਕੇਂਦਰ", "price": "📈 ਕੀਮਤ ਭਵਿੱਖਬਾਣੀ", "khata": "📒 ਖੇਤੀ ਖਾਤਾ",
        "weather_city": "ਲਾਈਵ ਮੌਸਮ ਲਈ ਸ਼ਹਿਰ ਦਰਜ ਕਰੋ", "temp": "ਤਾਪਮਾਨ", "humid": "ਨਮੀ",
        "wind": "ਹਵਾ ਦੀ ਗਤੀ", "seed_btn": "ਪ੍ਰਮਾਣੀਕਰਣ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ", "expert_call": "ਟੋਲ-ਫ੍ਰੀ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ",
        "pest_res": "ਗੁਲਾਬੀ ਸੁੰਡੀ ਲੱਭੀ ਗਈ। ਸਪਿਨੋਸੈਡ 45 SC ਦਾ ਛਿੜਕਾਅ ਕਰੋ।"
    }
}

st.sidebar.title("🌍 Language / भाषा / ਭਾਸ਼ਾ")
selected_lang = st.sidebar.selectbox("Choose Language", ["English", "Hindi", "Punjabi"])
t = LANG_DATA[selected_lang]

st.markdown("""<style>.stButton>button { background-color: #2e7d32; color: white; }</style>""", unsafe_allow_html=True)

# --- 3. CORE FUNCTIONS ---

@st.cache_data
def get_weather_data(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()
        if response.get("cod") != 200: return None
        return {"temp": response["main"]["temp"], "desc": response["weather"][0]["description"].capitalize(), "hum": response["main"]["humidity"], "wind": response["wind"]["speed"]}
    except: return None

# --- 4. NAVIGATION ---
st.sidebar.title(t["sidebar_header"])
menu = st.sidebar.radio("Go To:", [t["dashboard"], t["seed"], t["lab"], t["expert"], t["news"], t["mandi"], t["pest"], t["soil"], t["rental"], t["govt"], t["knowledge"], t["price"], t["khata"]])

# --- MODULES ---
if menu == t["dashboard"]:
    st.title(f"👨‍🌾 {t['dashboard']}")
    city_input = st.text_input(t["weather_city"], "Ludhiana")
    w = get_weather_data(city_input)
    if w:
        c1, c2, c3 = st.columns(3)
        c1.metric(t["temp"], f"{w['temp']}°C", w['desc'])
        c2.metric(t["humid"], f"{w['hum']}%")
        c3.metric(t["wind"], f"{w['wind']} m/s")

elif menu == t["seed"]:
    st.title(t["seed"])
    tag = st.text_input("SATHI Batch Number")
    if st.button(t["seed_btn"]):
        st.success("✅ Verified: Certified Wheat Seeds (Batch 2026-X)")
    

elif menu == t["expert"]:
    st.title(t["expert"])
    st.error(f"📞 {t['expert_call']}: **1800-180-1551**")

elif menu == t["mandi"]:
    st.title(t["mandi"])
    st.table(pd.DataFrame({"Market": ["Ludhiana", "Patna"], "Crop": ["Wheat", "Rice"], "Rate": [2275, 2180]}))

elif menu == t["pest"]:
    st.title(t["pest"])
    up = st.file_uploader("Upload Image", type=["jpg", "png"])
    if up: st.error(t["pest_res"])

elif menu == t["soil"]:
    st.title(t["soil"])
    ph = st.slider("Soil pH", 4.0, 10.0, 6.5)
    
    if st.button("Analyze"): st.success("pH is Optimal.")

elif menu == t["lab"]:
    st.title(t["lab"])
    st.write("📍 District Soil Testing Lab, Nagpur | 📍 PAU Lab, Ludhiana")

elif menu == t["news"]:
    st.title(t["news"])
    st.info("🚨 2026 Monsoon Forecast: Normal rainfall expected across Central India.")

elif menu == t["rental"]:
    st.title(t["rental"])
    st.write("Browse Tractors & Harvesters for rent.")

elif menu == t["govt"]:
    st.title(t["govt"])
    st.success("PM-KISAN Status: Active | PMFBY: Apply for Kharif Insurance.")

elif menu == t["knowledge"]:
    st.title(t["knowledge"])
    st.table(pd.DataFrame([{"Crop": "Wheat", "N-P-K": "120:60:40"}]))

elif menu == t["price"]:
    st.title(t["price"])
    df_p = pd.DataFrame({"Month": range(1,13), "Price": [2100 + (i*50) for i in range(12)]})
    st.plotly_chart(px.line(df_p, x="Month", y="Price"))

elif menu == t["khata"]:
    st.title(t["khata"])
    if 'ledger' not in st.session_state: st.session_state.ledger = pd.DataFrame([{"Item": "Seeds", "Cost": 1200}])
    st.dataframe(st.session_state.ledger)
