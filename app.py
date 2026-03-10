import streamlit as st
from fpdf import FPDF

# --- ALL INDIA DATA ---
INDIA_REGIONS = {
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
    "Maharashtra": ["Mumbai", "Pune"],
    "Manipur": ["Imphal"],
    "Meghalaya": ["Shillong"],
    "Mizoram": ["Aizawl"],
    "Nagaland": ["Kohima"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
    "Punjab": ["Chandigarh", "Ludhiana"],
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
    "Dadra & Nagar Haveli": ["Silvassa"],
    "Delhi": ["New Delhi", "North Delhi"],
    "Jammu & Kashmir": ["Srinagar", "Jammu"],
    "Ladakh": ["Leh", "Kargil"],
    "Lakshadweep": ["Kavaratti"],
    "Puducherry": ["Puducherry City"]
}

# --- PDF GENERATOR LOGIC ---
def generate_pdf(name, crop, state, selected_schemes):
    pdf = FPDF()
    pdf.add_page()
    
    # Branding
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(34, 139, 34) # Forest Green
    pdf.cell(200, 10, "ASES: Agri-Smart Personalized Advisory", ln=True, align='C')
    pdf.ln(10)
    
    # Farmer Profile
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Farmer Name: {name}", ln=True)
    pdf.cell(0, 10, f"State: {state} | Targeted Crop: {crop}", ln=True)
    pdf.ln(5)
    pdf.line(10, 50, 200, 50)
    
    # Schemes Content
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Selected Government Schemes & Benefits:", ln=True)
    
    pdf.set_font("Arial", '', 11)
    for s in selected_schemes:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"• {s}", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 7, f"{SCHEME_DETAILS[s]}\n")
        pdf.ln(2)
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Disclaimer: Data generated for educational purposes - IIT Patna Group 32", align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- APP UI ---
st.set_page_config(page_title="ASES All-India Hub", layout="wide")
st.title("🇮🇳 Agri-Smart Ecosystem: Knowledge Hub")

# Inputs
c1, c2, c3 = st.columns(3)
with c1:
    u_name = st.text_input("Farmer Name", "Aditi Dwivedi")
with c2:
    u_state = st.selectbox("State/UT", sorted(INDIA_REGIONS.keys()))
with c3:
    u_crop = st.text_input("Focus Crop", "Wheat")

st.divider()

# Multi-Scheme Selection
st.subheader("Select All Relevant Schemes")
all_scheme_names = list(SCHEME_DETAILS.keys())
u_selections = st.multiselect("Choose as many as apply:", all_scheme_names, help="Select multiple schemes to include in your PDF report.")

if u_selections:
    # Preview
    for s in u_selections:
        with st.expander(f"📖 {s}"):
            st.write(SCHEME_DETAILS[s])
    
    # Download Action
    pdf_bytes = generate_pdf(u_name, u_crop, u_state, u_selections)
    st.download_button(
        label="📥 Download Personalized Multi-Scheme Guide",
        data=pdf_bytes,
        file_name=f"{u_name}_All_Schemes.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.info("Please select at least one scheme to generate the PDF report.")
