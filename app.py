# ★ Murlidhar Academy MCQ Generator (Textbook Stacked Fraction + Toggle) ★

import streamlit as st
import re
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import tempfile
import requests
import os

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

st.set_page_config(page_title="Murlidhar MCQ Generator", layout="wide")

st.title("📄 Murlidhar Academy MCQ Generator (Textbook Maths Engine)")

DEFAULT_TEMPLATE_URL = "https://docs.google.com/document/d/1JMow6oJ2ASJah5vM4OK1Q-uYPefiMnEg/export?format=docx"

# -------------------------------------------------
# SUBJECT TOGGLE
# -------------------------------------------------

subject = st.selectbox("Select Subject", ["Other Subject", "Maths"])

math_mode = (subject == "Maths")

# -------------------------------------------------
# STACKED FRACTION ENGINE
# -------------------------------------------------

def add_stacked_fraction(paragraph, numerator, denominator):

    omath = OxmlElement('m:oMath')
    fraction = OxmlElement('m:f')

    num = OxmlElement('m:num')
    num_run = OxmlElement('m:r')
    num_text = OxmlElement('m:t')
    num_text.text = numerator
    num_run.append(num_text)
    num.append(num_run)

    den = OxmlElement('m:den')
    den_run = OxmlElement('m:r')
    den_text = OxmlElement('m:t')
    den_text.text = denominator
    den_run.append(den_text)
    den.append(den_run)

    fraction.append(num)
    fraction.append(den)
    omath.append(fraction)

    paragraph._element.append(omath)

# -------------------------------------------------
# MATH FORMATTER (ONLY BASIC CLEAN)
# -------------------------------------------------

def clean_text(text):
    if not text:
        return ""
    text = text.replace("$", "")
    text = text.replace("\\times", "×")
    text = text.replace("\\div", "÷")
    text = text.replace("\\infty", "∞")
    return text

# -------------------------------------------------
# PARSE MCQ
# -------------------------------------------------

def parse_mcq_text(raw_text):

    question_pattern = re.compile(r'(?=\(\d{2}\))')
    blocks = question_pattern.split(raw_text)

    parsed_questions = []

    for block in blocks:

        if not block.strip():
            continue

        q_num_match = re.search(r'\((\d{2})\)', block)
        if not q_num_match:
            continue

        parts = re.split(r'\(A\)', block, maxsplit=1)

        raw_q_text = parts[0].replace(q_num_match.group(0), '')
        q_text_clean = clean_text(raw_q_text)

        options_part = ""
        if len(parts) > 1:
            options_part = "(A) " + parts[1]

        def extract_option(label1, label2=None):
            if label2:
                pattern = rf'\({label1}\)(.*?)\({label2}\)'
            else:
                pattern = rf'\({label1}\)(.*)'
            match = re.search(pattern, options_part, re.DOTALL)
            return clean_text(match.group(1)) if match else ""

        parsed_questions.append({
            "q_num": q_num_match.group(1),
            "question": q_text_clean,
            "A": extract_option("A", "B"),
            "B": extract_option("B", "C"),
            "C": extract_option("C", "D"),
            "D": extract_option("D", None)
        })

    return parsed_questions

# -------------------------------------------------
# CREATE DOC
# -------------------------------------------------

def create_doc(template_path, questions_data):

    try:
        doc = Document(template_path)
    except:
        doc = Document()

    def set_font(run):
        run.font.name = 'HindVadodara'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'HindVadodara')
        run.font.size = Pt(11)

    for q in questions_data:

        p = doc.add_paragraph()

        run_num = p.add_run(f"({q['q_num']}) ")
        set_font(run_num)

        if math_mode and "\\frac" in q["question"]:
            frac_match = re.search(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', q["question"])
            if frac_match:
                add_stacked_fraction(p, frac_match.group(1), frac_match.group(2))
            else:
                p.add_run(q["question"])
        else:
            p.add_run(q["question"])

        p.add_run().add_break()

        for label in ["A", "B", "C", "D"]:
            p.add_run(f"({label}) ")
            set_font(p.runs[-1])
            p.add_run(q[label])
            if label in ["A", "B"]:
                p.add_run("\t")
            else:
                p.add_run().add_break()

    output_filename = "Murlidhar_Final_Pro.docx"
    doc.save(output_filename)
    return output_filename

# -------------------------------------------------
# UI
# -------------------------------------------------

uploaded_template = st.file_uploader("Upload .docx template (optional)", type=["docx"])
mcq_text = st.text_area("Paste MCQs Here", height=300)

if st.button("Generate Paper"):

    if not mcq_text.strip():
        st.error("Please paste MCQs.")
        st.stop()

    if uploaded_template:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_template.read())
            template_path = tmp.name
    else:
        response = requests.get(DEFAULT_TEMPLATE_URL)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(response.content)
            template_path = tmp.name

    q_data = parse_mcq_text(mcq_text)
    final_file = create_doc(template_path, q_data)

    with open(final_file, "rb") as f:
        st.download_button("Download File", f, file_name="Murlidhar_Final_Pro.docx")

    os.remove(template_path)
