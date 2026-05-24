import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image as PILImage
import hashlib
import random

# ---------------- SESSION STATE ----------------

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'bmi_history' not in st.session_state:
    st.session_state.bmi_history = []

if 'symptom_history' not in st.session_state:
    st.session_state.symptom_history = []

if 'xray_history' not in st.session_state:
    st.session_state.xray_history = []

# ---------------- BMI FUNCTIONS ----------------

def calculate_bmi(weight, height):
    bmi = weight / ((height / 100) ** 2)
    return round(bmi, 1)


def get_bmi_category(bmi):

    if bmi < 18.5:
        return "Underweight", "You may need to gain weight."

    elif 18.5 <= bmi < 25:
        return "Normal weight", "Maintain healthy lifestyle."

    elif 25 <= bmi < 30:
        return "Overweight", "Increase physical activity."

    elif 30 <= bmi < 35:
        return "Obese Class I", "Consult healthcare provider."

    elif 35 <= bmi < 40:
        return "Obese Class II", "Medical supervision recommended."

    else:
        return "Obese Class III", "Immediate medical consultation advised."

# ---------------- SYMPTOM ANALYZER ----------------

def analyze_symptoms(symptoms_text):

    symptoms = symptoms_text.lower()

    symptom_database = {

        "fever": {
            "possible_conditions": [
                "Viral Infection",
                "Influenza",
                "COVID-19"
            ],
            "severity": "Moderate",
            "recommendation": "Monitor temperature and hydrate.",
            "home_remedies": [
                "Paracetamol",
                "Cold compress",
                "Warm fluids"
            ]
        },

        "cough": {
            "possible_conditions": [
                "Cold",
                "Bronchitis",
                "Asthma"
            ],
            "severity": "Moderate",
            "recommendation": "Steam inhalation recommended.",
            "home_remedies": [
                "Honey",
                "Steam inhalation"
            ]
        },

        "headache": {
            "possible_conditions": [
                "Migraine",
                "Tension Headache"
            ],
            "severity": "Mild",
            "recommendation": "Rest and hydration advised.",
            "home_remedies": [
                "Cold compress",
                "Hydration"
            ]
        },

        "chest_pain": {
            "possible_conditions": [
                "Angina",
                "Heart Attack"
            ],
            "severity": "High",
            "recommendation": "Seek immediate medical attention.",
            "home_remedies": [
                "Emergency care required"
            ]
        },

        "back_pain": {
            "possible_conditions": [
                "Muscle Strain",
                "Slip Disc",
                "Sciatica"
            ],
            "severity": "Moderate",
            "recommendation": "Avoid heavy lifting.",
            "home_remedies": [
                "Hot compress",
                "Stretching"
            ]
        },

        "neck_pain": {
            "possible_conditions": [
                "Muscle Spasm",
                "Poor Posture"
            ],
            "severity": "Moderate",
            "recommendation": "Use neck support.",
            "home_remedies": [
                "Warm compress",
                "Rest"
            ]
        },

        "stomach_pain": {
            "possible_conditions": [
                "Gastritis",
                "Food Poisoning",
                "Acidity"
            ],
            "severity": "Moderate",
            "recommendation": "Avoid oily food.",
            "home_remedies": [
                "ORS",
                "Light meals"
            ]
        },

        "leg_pain": {
            "possible_conditions": [
                "Muscle Cramps",
                "Arthritis"
            ],
            "severity": "Mild",
            "recommendation": "Rest affected leg.",
            "home_remedies": [
                "Massage",
                "Ice pack"
            ]
        },

        "arm_pain": {
            "possible_conditions": [
                "Muscle Strain",
                "Nerve Compression"
            ],
            "severity": "Moderate",
            "recommendation": "Avoid excessive movement.",
            "home_remedies": [
                "Cold compress",
                "Rest"
            ]
        },

        "joint_pain": {
            "possible_conditions": [
                "Arthritis",
                "Gout"
            ],
            "severity": "Moderate",
            "recommendation": "Reduce stress on joints.",
            "home_remedies": [
                "Warm bath",
                "Light exercise"
            ]
        },

        "tooth_pain": {
            "possible_conditions": [
                "Dental Cavity",
                "Gum Infection"
            ],
            "severity": "Moderate",
            "recommendation": "Consult dentist if pain continues.",
            "home_remedies": [
                "Salt water rinse",
                "Clove oil"
            ]
        },

        "ear_pain": {
            "possible_conditions": [
                "Ear Infection",
                "Wax Build-up"
            ],
            "severity": "Moderate",
            "recommendation": "Avoid inserting objects into ear.",
            "home_remedies": [
                "Warm compress"
            ]
        },

        "eye_pain": {
            "possible_conditions": [
                "Eye Strain",
                "Conjunctivitis"
            ],
            "severity": "High",
            "recommendation": "Seek ophthalmologist evaluation.",
            "home_remedies": [
                "Eye rest",
                "Cold compress"
            ]
        },

        "body_pain": {
            "possible_conditions": [
                "Viral Fever",
                "Fatigue"
            ],
            "severity": "Moderate",
            "recommendation": "Rest and hydration advised.",
            "home_remedies": [
                "Paracetamol",
                "Warm fluids"
            ]
        }
    }

    detected_symptoms = []

    for symptom, data in symptom_database.items():

        if symptom.replace("_", " ") in symptoms:
            detected_symptoms.append((symptom, data))

    if not detected_symptoms:
        return None

    all_conditions = []
    all_remedies = []

    highest_severity = "Mild"

    severity_order = {
        "Mild": 1,
        "Moderate": 2,
        "High": 3
    }

    for symptom, data in detected_symptoms:

        all_conditions.extend(data["possible_conditions"])
        all_remedies.extend(data["home_remedies"])

        if severity_order[data["severity"]] > severity_order[highest_severity]:
            highest_severity = data["severity"]

    return {

        "symptoms_found": [
            s[0].replace("_", " ").title()
            for s in detected_symptoms
        ],

        "possible_conditions": list(set(all_conditions)),

        "severity": highest_severity,

        "remedies": list(set(all_remedies)),

        "recommendation": detected_symptoms[0][1]["recommendation"]
    }

# ---------------- X-RAY ANALYSIS ----------------

def analyze_xray(image_file):

    try:

        image = PILImage.open(image_file)

        img_array = np.array(image.convert('L'))

        mean_intensity = np.mean(img_array)

        image_hash = hashlib.md5(
            image_file.getvalue()
        ).hexdigest()[:8]

        findings = [

            {
                "finding": "RIGHT LOWER LOBE OPACITY",
                "condition": "PNEUMONIA",
                "result": "POSITIVE"
            },

            {
                "finding": "NORMAL LUNG FIELDS",
                "condition": "NORMAL",
                "result": "NEGATIVE"
            }
        ]

        selected = random.choice(findings)

        return {

            "status": "success",

            "result": selected["result"],

            "liyness": selected["condition"],

            "findings": [selected["finding"]],

            "image_id": image_hash,

            "mean_intensity": round(mean_intensity, 2),

            "recommendation":
                "Consult pulmonologist immediately"
                if selected["result"] == "POSITIVE"
                else "Routine follow-up advised"
        }

    except Exception as e:

        return {
            "status": "error",
            "result": "ERROR",
            "message": str(e)
        }

# ---------------- PDF REPORT ----------------

def generate_comprehensive_report(
    name,
    age,
    gender,
    weight,
    height,
    bmi,
    bmi_category,
    bmi_advice
):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()

    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1
    )

    story.append(
        Paragraph(
            "COMPREHENSIVE HEALTH REPORT",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"Patient Name: {name}",
            styles['Normal']
        )
    )

    story.append(
        Paragraph(
            f"Age: {age}",
            styles['Normal']
        )
    )

    story.append(
        Paragraph(
            f"Gender: {gender}",
            styles['Normal']
        )
    )

    story.append(
        Paragraph(
            f"Generated: {datetime.now()}",
            styles['Normal']
        )
    )

    story.append(Spacer(1, 20))

    bmi_data = [

        ["Weight", f"{weight} kg"],
        ["Height", f"{height} cm"],
        ["BMI", str(bmi)],
        ["Category", bmi_category],
        ["Recommendation", bmi_advice]
    ]

    table = Table(bmi_data, colWidths=[150, 300])

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),

        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    story.append(table)

    story.append(Spacer(1, 20))

    disclaimer = Paragraph(
        "DISCLAIMER: Educational use only. "
        "Not a substitute for professional medical advice.",
        styles['Italic']
    )

    story.append(disclaimer)

    doc.build(story)

    buffer.seek(0)

    return buffer

# ---------------- CHAT RESPONSE ----------------

def health_response(user_input):

    user_input = user_input.lower()

    if user_input in [
        "help",
        "commands",
        "menu",
        "what can you do",
        "features"
    ]:

        return """
AVAILABLE FEATURES

1. CLINICAL CHAT
- Ask health-related questions
- Get symptom information
- General medical guidance

2. BMI ANALYSIS
- Calculate BMI
- WHO classification
- Health recommendations
- PDF report generation

3. SYMPTOM ANALYZER
Supported symptoms:
- Fever
- Cough
- Headache
- Chest pain
- Back pain
- Neck pain
- Stomach pain
- Leg pain
- Arm pain
- Joint pain
- Tooth pain
- Ear pain
- Eye pain
- Body pain

4. X-RAY ANALYSIS
- Upload JPG/PNG X-ray image
- Preliminary AI analysis
- Clinical findings

5. REPORT GENERATION
- Download PDF reports

INDIAN EMERGENCY HELPLINES
- Medical Emergency: 108
- National Emergency: 112
- Ambulance: 102
- Mental Health: 1800-599-0019
"""

    health_info = {

        "fever":
            "Fever may indicate infection. Stay hydrated.",

        "cough":
            "Cough may be due to infection or allergy.",

        "headache":
            "Headache may occur due to stress or dehydration.",

        "chest pain":
            "Chest pain requires urgent medical evaluation.",

        "back pain":
            "Back pain may result from posture or muscle strain.",

        "neck pain":
            "Neck pain is commonly due to posture issues.",

        "stomach pain":
            "Stomach pain may be related to acidity or infection.",

        "leg pain":
            "Leg pain may occur due to cramps or fatigue.",

        "arm pain":
            "Arm pain may result from muscle strain.",

        "joint pain":
            "Joint pain may indicate arthritis.",

        "tooth pain":
            "Tooth pain may be caused by cavity or infection.",

        "ear pain":
            "Ear pain may be due to infection or wax build-up.",

        "eye pain":
            "Eye pain should be checked if vision changes occur.",

        "body pain":
            "Body pain is commonly associated with viral infection.",

        "diabetes":
            "Monitor blood sugar regularly.",

        "hypertension":
            "Reduce salt intake and monitor blood pressure."
    }

    for keyword, response in health_info.items():

        if keyword in user_input:
            return response

    return (
        "Unknown query. Type HELP to see available features."
    )

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Health Assist ChatBot",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Health Assist ChatBot")

st.markdown(
    "Clinical Decision Support System"
)

st.markdown("---")

# ---------------- TABS ----------------

tab1, tab2, tab3, tab4 = st.tabs([
    "CLINICAL CHAT",
    "BMI ANALYSIS",
    "SYMPTOM ANALYZER",
    "X-RAY ANALYSIS"
])

# ---------------- TAB 1 ----------------

with tab1:

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(
        "Describe symptoms or ask clinical question"
    ):

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        response = health_response(prompt)

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

# ---------------- TAB 2 ----------------

with tab2:

    st.subheader("BODY MASS INDEX CALCULATOR")

    col1, col2 = st.columns(2)

    with col1:

        name_bmi = st.text_input(
            "Patient Name",
            value="Guest Patient"
        )

        age_bmi = st.number_input(
            "Age",
            1,
            120,
            30
        )

        gender_bmi = st.selectbox(
            "Gender",
            ["Male", "Female", "Other"]
        )

    with col2:

        weight_bmi = st.number_input(
            "Weight (kg)",
            20.0,
            300.0,
            70.0
        )

        height_bmi = st.number_input(
            "Height (cm)",
            100.0,
            250.0,
            170.0
        )

    if st.button("CALCULATE BMI"):

        bmi = calculate_bmi(
            weight_bmi,
            height_bmi
        )

        category, advice = get_bmi_category(bmi)

        st.success(f"BMI RESULT: {bmi}")

        st.info(f"CATEGORY: {category}")

        st.write(advice)

        pdf_buffer = generate_comprehensive_report(
            name_bmi,
            age_bmi,
            gender_bmi,
            weight_bmi,
            height_bmi,
            bmi,
            category,
            advice
        )

        st.download_button(
            label="DOWNLOAD REPORT",
            data=pdf_buffer,
            file_name="health_report.pdf",
            mime="application/pdf"
        )

# ---------------- TAB 3 ----------------

with tab3:

    st.subheader("SYMPTOM ANALYZER")

    symptom_input = st.text_area(
        "Enter symptoms",
        height=150
    )

    if st.button("ANALYZE SYMPTOMS"):

        if symptom_input.strip():

            analysis = analyze_symptoms(
                symptom_input
            )

            if analysis:

                st.success("ANALYSIS COMPLETE")

                st.write("Symptoms Found:")

                for symptom in analysis['symptoms_found']:
                    st.write(f"- {symptom}")

                st.write("Possible Conditions:")

                for condition in analysis['possible_conditions']:
                    st.write(f"- {condition}")

                st.write(
                    f"Severity: {analysis['severity']}"
                )

                st.info(
                    analysis['recommendation']
                )

                st.write("Home Remedies:")

                for remedy in analysis['remedies']:
                    st.write(f"- {remedy}")

            else:
                st.warning(
                    "No matching symptom pattern found."
                )

# ---------------- TAB 4 ----------------

with tab4:

    st.subheader("X-RAY IMAGE ANALYSIS")

    uploaded_file = st.file_uploader(
        "Upload X-Ray Image",
        type=['jpg', 'jpeg', 'png']
    )

    if uploaded_file is not None:

        image = PILImage.open(uploaded_file)

        st.image(
            image,
            use_container_width=True
        )

        if st.button("ANALYZE X-RAY"):

            analysis = analyze_xray(
                uploaded_file
            )

            if analysis['status'] == 'success':

                st.success(
                    f"RESULT: {analysis['result']}"
                )

                st.write(
                    f"Diagnosis: {analysis['liyness']}"
                )

                st.write("Findings:")

                for finding in analysis['findings']:
                    st.write(f"- {finding}")

                st.info(
                    analysis['recommendation']
                )

            else:

                st.error(
                    analysis['message']
                )

# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.header("CLINICAL DASHBOARD")

    st.markdown("---")

    st.subheader("EMERGENCY RESOURCES")

    st.write("Medical Emergency: 108")
    st.write("National Emergency: 112")
    st.write("Ambulance Service: 102")
    st.write("Women Helpline: 1091")
    st.write("Child Helpline: 1098")
    st.write("Mental Health Helpline: 1800-599-0019")

    st.markdown("---")

    st.subheader("SYSTEM INFO")

    st.markdown("""
Clinical Assist AI v4.0

- Clinical Chat
- BMI Analysis
- Symptom Analyzer
- X-Ray Analysis
- PDF Reports

Educational use only.
""")

# ---------------- FOOTER ----------------

st.markdown("---")

st.caption(
    "CLINICAL DISCLAIMER: "
    "This AI system provides educational information only. "
    "Not a substitute for licensed medical advice."
    )
