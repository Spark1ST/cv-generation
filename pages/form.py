import streamlit as st
import sys
import os
import base64
from io import BytesIO

import markdown
import streamlit.components.v1 as components

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------------------------
# Import CV Engine (CrewAI backend)
# -------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cv_generator import generate_cv_and_evaluation

# -------------------------------------------------
# Utilities
# -------------------------------------------------
def safe_filename(name: str) -> str:
    name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    return "_".join(name.split()) + "_CV.pdf" if name else "CV.pdf"


# -------------------------------------------------
# HTML VIEW (MARKDOWN → HTML → NEW TAB)
# -------------------------------------------------
def open_cv_markdown_new_tab(cv_md: str, name: str):
    body_html = markdown.markdown(cv_md, extensions=["extra", "sane_lists"])

    html_page = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{name or "CV"} – CV</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial;
  background: #f5f6f8;
  padding: 24px;
}}
.cv {{
  max-width: 900px;
  margin: auto;
  background: #fff;
  padding: 36px;
  border-radius: 10px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.06);
}}
h1 {{ font-size: 26px; }}
h2 {{
  font-size: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 4px;
  margin-top: 22px;
}}
p, li {{
  font-size: 14px;
  line-height: 1.6;
}}
</style>
</head>
<body>
<div class="cv">
{body_html}
</div>
</body>
</html>
"""

    b64 = base64.b64encode(html_page.encode("utf-8")).decode("utf-8")

    components.html(
        f"""
        <button id="openCv">View CV (HTML – New Tab)</button>
        <script>
            const html = atob("{b64}");
            const blob = new Blob([html], {{ type: "text/html" }});
            const url = URL.createObjectURL(blob);
            document.getElementById("openCv").onclick = () => window.open(url, "_blank");
        </script>
        """,
        height=60
    )


# -------------------------------------------------
# PDF GENERATOR (FROM MARKDOWN)
# -------------------------------------------------
def generate_pdf_from_markdown(cv_md: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for line in cv_md.split("\n"):
        line = line.strip()

        if not line:
            story.append(Spacer(1, 8))
            continue

        if line.startswith("# "):
            story.append(Paragraph(f"<b>{line[2:]}</b>", styles["Title"]))
        elif line.startswith("## "):
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>{line[3:]}</b>", styles["Heading2"]))
        elif line.startswith("- "):
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(line[2:], styles["Normal"]))],
                    bulletType="bullet"
                )
            )
        else:
            story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


# -------------------------------------------------
# STREAMLIT APP
# -------------------------------------------------
def main():
    st.set_page_config(page_title="AI CV Generator", layout="centered")
    st.title("AI CV Generator")

    # --- Session State ---
    for key in ["name", "experience", "education", "skills", "cv_md", "eval_md"]:
        st.session_state.setdefault(key, "")

    # --- Inputs ---
    st.text_input("Full Name", key="name")
    st.text_area("Experience", key="experience", height=150)
    st.text_area("Education", key="education", height=120)
    st.text_area("Skills (comma-separated)", key="skills")

    # --- Generate ---
    if st.button("Generate CV"):
        with st.spinner("Generating CV..."):

            # 🔒 INPUT NORMALIZATION (CRITICAL FIX)
            user_data = {}

            if st.session_state.name.strip():
                user_data["name"] = st.session_state.name.strip()

            if st.session_state.experience.strip():
                user_data["experience"] = st.session_state.experience.strip()

            if st.session_state.education.strip():
                user_data["education"] = st.session_state.education.strip()

            skills = [
                s.strip()
                for s in st.session_state.skills.split(",")
                if s.strip()
            ]
            if skills:
                user_data["skills"] = skills

            if not user_data:
                st.error("Please enter at least one field to generate a CV.")
                return

            cv_md, eval_md = generate_cv_and_evaluation(user_data, "")

            # 🛡 Guard against silent failure
            if not cv_md:
                st.error("CV generation failed. Please try again.")
                return

            st.session_state.cv_md = cv_md
            st.session_state.eval_md = eval_md or ""

    # --- Output ---
    if st.session_state.cv_md:
        st.subheader("CV Preview")
        st.markdown(st.session_state.cv_md)

        col1, col2 = st.columns(2)

        with col1:
            open_cv_markdown_new_tab(
                st.session_state.cv_md,
                st.session_state.name
            )

        with col2:
            st.download_button(
                label="Download CV (PDF)",
                data=generate_pdf_from_markdown(st.session_state.cv_md),
                file_name=safe_filename(st.session_state.name),
                mime="application/pdf"
            )

        if st.session_state.eval_md:
            st.subheader("Career Match Evaluation")
            st.markdown(st.session_state.eval_md)


if __name__ == "__main__":
    main()