# ★ Murlidhar Academy: Final Logic (Pro Spacing) - Streamlit Version ★

import streamlit as st
import re
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
import tempfile
import os

st.set_page_config(page_title="Murlidhar MCQ Formatter", layout="wide")

st.title("📄 Murlidhar Academy MCQ Paper Generator (Pro Spacing)")

# --- 1. Text Cleaner Function ---
def clean_garbage_text(text, keep_pipe=False):
    if not text:
        return ""

    text = re.sub(r'\[cite.*?\]', '', text)
    text = re.sub(r'\[source.*?\]', '', text)
    text = re.sub(r'\[cite_start\]', '', text)
    text = text.replace('*', '').replace('\\', '')

    if not keep_pipe:
        text = text.replace('|', '')

    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n+', '\n', text)

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        clean_line = re.sub(r'\s+', ' ', line).strip()
        if clean_line:
            cleaned_lines.append(clean_line)

    return "\n".join(cleaned_lines)


# --- 2. Parse MCQ Logic ---
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
        q_text_clean = clean_garbage_text(raw_q_text, keep_pipe=True)

        options_part = ""
        if len(parts) > 1:
            options_part = "(A) " + parts[1]

        match_a = re.search(r'\(A\)(.*?)\(B\)', options_part, re.DOTALL)
        opt_a = clean_garbage_text(match_a.group(1), False) if match_a else ""

        match_b = re.search(r'\(B\)(.*?)\(C\)', options_part, re.DOTALL)
        opt_b = clean_garbage_text(match_b.group(1), False) if match_b else ""

        match_c = re.search(r'\(C\)(.*?)\(D\)', options_part, re.DOTALL)
        opt_c = clean_garbage_text(match_c.group(1), False) if match_c else ""

        match_d = re.search(r'\(D\)(.*)', options_part, re.DOTALL)
        opt_d = clean_garbage_text(match_d.group(1), False) if match_d else ""

        parsed_questions.append({
            "q_num": q_num_match.group(1),
            "question": q_text_clean,
            "A": opt_a,
            "B": opt_b,
            "C": opt_c,
            "D": opt_d
        })

    return parsed_questions


# --- 3. Word File Creation ---
def create_doc(template_path, questions_data):

    try:
        doc = Document(template_path)
    except:
        doc = Document()

    def set_font(run):
        font_name = 'HindVadodara'
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
        run.font.size = Pt(11)
        run.font.bold = False

    def add_text(paragraph, text):
        parts = text.split('\n')
        for i, part in enumerate(parts):
            run = paragraph.add_run(part)
            set_font(run)
            if i < len(parts) - 1:
                paragraph.add_run().add_break()

    def get_separator(length):
        if length > 18:
            return "SOFT_ENTER"
        elif 15 <= length <= 17:
            return "TAB_1"
        elif 9 <= length <= 14:
            return "TAB_2"
        else:
            return "SPACE_5"

    for q in questions_data:

        p = doc.add_paragraph()

        run_num = p.add_run(f"({q['q_num']}) ")
        set_font(run_num)
        add_text(p, q['question'])
        p.add_run().add_break()

        len_a = len(q['A'])
        len_b = len(q['B'])
        len_c = len(q['C'])
        len_d = len(q['D'])

        all_short = (len_a <= 8 and len_b <= 8 and len_c <= 8 and len_d <= 8)

        if all_short:
            for label in ["A", "B", "C", "D"]:
                p.add_run(f"({label}) ")
                set_font(p.runs[-1])
                add_text(p, q[label])
                if label != "D":
                    p.add_run("     ")
                    set_font(p.runs[-1])
        else:
            for label in ["A", "B"]:
                p.add_run(f"({label}) ")
                set_font(p.runs[-1])
                add_text(p, q[label])
                p.add_run("\t")
                set_font(p.runs[-1])

            p.add_run().add_break()

            for label in ["C", "D"]:
                p.add_run(f"({label}) ")
                set_font(p.runs[-1])
                add_text(p, q[label])
                if label == "C":
                    p.add_run("\t")
                    set_font(p.runs[-1])

    output_filename = "Murlidhar_Final_Pro.docx"
    doc.save(output_filename)
    return output_filename


# --- UI Section ---

template_file = st.file_uploader("📂 Upload Word Template (.docx)", type=["docx"])

mcq_text = st.text_area(
    "✍️ Paste Raw MCQs Text",
    height=300,
    placeholder="(01) Question\n(A) Option1 (B) Option2 (C) Option3 (D) Option4"
)

if st.button("🚀 Generate Paper"):

    if not template_file or not mcq_text.strip():
        st.error("❌ Please upload template and paste MCQs.")
    else:
        with st.spinner("Processing..."):

            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(template_file.read())
                template_path = tmp.name

            q_data = parse_mcq_text(mcq_text)
            final_file = create_doc(template_path, q_data)

            with open(final_file, "rb") as f:
                st.download_button(
                    "📥 Download Final Paper",
                    f,
                    file_name="Murlidhar_Final_Pro.docx"
                )

            os.remove(template_path)
