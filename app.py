import streamlit as st
from fpdf import FPDF
import pandas as pd

# --- 1. FULL DATABASE (28 States & 8 UTs) ---
INDIA_DATA = {
    "Andhra Pradesh": ["Amaravati", "Visakhapatnam", "Vijayawada"],
    "Arunachal Pradesh": ["Itanagar", "Tawang"],
    "Assam": ["Dispur", "Guwahati"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bihta"],
    "Chhattisgarh": ["Raipur", "Bhilai"],
    "Goa": ["Panaji", "Margao"],
    "Gujarat": ["Gandhinagar", "Ahmedabad"],
    "Haryana": ["Chandigarh", "Gurugram"],
    "Himachal Pradesh": ["Shimla", "Dharamshala"],
    "Jharkhand": ["Ranchi", "Jamshedpur"],
    "Karnataka": ["Bengaluru", "Mysuru"],
    "Kerala": ["Thiruvananthapuram", "Kochi"],
    "Madhya Pradesh": ["Bhopal", "Indore"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Manipur": ["Imphal"], "Meghalaya": ["Shillong"], "Mizoram": ["Aizawl"], "Nagaland": ["Kohima"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
    "Punjab": ["Chandigarh", "Ludhiana", "Amritsar"],
    "Rajasthan": ["Jaipur", "Jodhpur"],
    "Sikkim": ["Gangtok"],
    "Tamil Nadu": ["Chennai", "Coimbatore"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Tripura": ["Agartala"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
    "Uttarakhand": ["Dehradun", "Haridwar"],
    "West Bengal": ["Kolkata", "Siliguri"],
    "Andaman & Nicobar": ["Port Blair"],
    "Chandigarh": ["Chandigarh City"],
    "Dadra & Nagar Haveli and Daman & Diu": ["Daman", "Silvassa"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi"],
    "Jammu & Kashmir": ["Srinagar", "Jammu"],
    "Ladakh": ["Leh", "Kargil"],
    "Lakshadweep": ["Kavaratti"],
    "Puducherry": ["Puducherry City"]
}

SCHEME_DETAILS = {
    "PM-Kisan": "Direct income support of Rs. 6,000 per year.",
    "Fasal Bima": "Crop insurance against natural calamities and pests.",
    "Kisan Credit Card": "Low-interest loans for seeds and fertilizers.",
    "PM-KUSUM": "Subsidy for solar irrigation pumps.",
    "Soil Health Card": "Nutrient analysis and fertilizer recommendations."
}

# --- 2. DYNAMIC PDF GENERATOR ---
def generate_personalized_pdf(name, crop, state, selected_schemes):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ASES: Personalized Agri-Guide", ln=True, align='C')
    pdf.ln(10)
    
    # User Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Farmer Name: {name}", ln=True)
    pdf.cell(0, 10, f"State: {state} | Focused Crop: {crop}", ln=True)
    pdf.ln(5)
    pdf.line(10, 50, 200, 50)
    
    # Content Section
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Selected Schemes & Benefits:", ln=True)
    
    pdf.set_font("Arial", '', 11)
    for s in selected_schemes:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"-> {s}", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, f"{SCHEME_DETAILS[s]}\n")
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN INTERFACE ---
st.set_page_config(page_title="ASES Group 32", layout="wide")
st.title("🌾 Agri-Smart Ecosystem Solutions")

# Sidebar Navigation
page = st.sidebar.selectbox("Go to Module:", ["🚜 Kisan Sampark (Rentals)", "📚 Knowledge Hub (Schemes)"])

if page == "🚜 Kisan Sampark (Rentals)":
    st.header("🚜 Find Equipment in Your City")
    col1, col2 = st.columns(2)
    with col1:
        st_choice = st.selectbox("State/UT", sorted(INDIA_DATA.keys()))
    with col2:
        ct_choice = st.selectbox("City", INDIA_DATA[st_choice])
    
    st.success(f"Listing machinery available in {ct_choice}, {st_choice}")
    
    # Mock Rental Card
    with st.container(border=True):
        c_left, c_right = st.columns([3, 1])
        c_left.write(f"**Heavy Tractor & Harvester**\n\nContact: Local Center - {ct_choice}")
        call_btn = f'<a href="tel:9876543210"><button style="background-color:green;color:white;width:100%;border:none;padding:10px;border-radius:5px;">📞 Call Owner</button></a>'
        c_right.markdown(call_btn, unsafe_allow_html=True)

elif page == "📚 Knowledge Hub (Schemes)":
    st.header("📚 Get Your Personalized Scheme Report")
    
    u_name = st.text_input("Full Name:", "Aditi Dwivedi")
    u_crop = st.text_input("Major Crop:", "Wheat")
    u_state = st.selectbox("Confirm State:", sorted(INDIA_DATA.keys()))
    
    st.write("### Choose Schemes to Include:")
    chosen_schemes = st.multiselect("Available Schemes", list(SCHEME_DETAILS.keys()))

    if st.button("Generate PDF Guide", use_container_width=True):
        if chosen_schemes:
            pdf_bytes = generate_personalized_pdf(u_name, u_crop, u_state, chosen_schemes)
            st.download_button(
                label="📥 Download My Personalized PDF",
                data=pdf_bytes,
                file_name=f"{u_name}_AgriReport.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.warning("Please select at least one scheme.")
