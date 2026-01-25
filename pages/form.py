import streamlit as st
import sys
import os
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cv_generator import generate_cv_and_evaluation


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def safe_filename(name: str) -> str:
    name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    return "_".join(name.split()) + "_CV.pdf" if name else "CV.pdf"


def build_cv_data():
    return {
        "name": st.session_state.name,
        "title": st.session_state.title,
        "location": st.session_state.location,
        "phone": st.session_state.phone,
        "email": st.session_state.email,
        "linkedin": st.session_state.linkedin,
        "education": st.session_state.education,
        "experience": st.session_state.experience,
        "projects": st.session_state.projects,
        "skills": st.session_state.skills,
    }


# -------------------------------------------------
# HTML VIEW (NEW TAB)
# -------------------------------------------------
def open_html_new_tab(cv):
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{cv['name']} CV</title>
    <style>
        body {{ font-family: Arial; margin: 40px; line-height: 1.6; }}
        h1 {{ text-align: center; }}
        h3 {{ border-bottom: 1px solid #333; }}
        pre {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>{cv['name']}</h1>
    <p style="text-align:center;">
        {cv['title']}<br>
        {cv['location']} | {cv['phone']} | {cv['email']} | {cv['linkedin']}
    </p>
    <hr>
    <h3>Education</h3><pre>{cv['education']}</pre>
    <h3>Experience</h3><pre>{cv['experience']}</pre>
    {f"<h3>Projects</h3><pre>{cv['projects']}</pre>" if cv['projects'].strip() else ""}
    <h3>Skills</h3><pre>{cv['skills']}</pre>
</body>
</html>
"""
    st.components.v1.html(
        f"""
        <script>
            const w = window.open("", "_blank");
            w.document.write(`{html.replace("`", "\\`")}`);
            w.document.close();
        </script>
        """,
        height=0
    )


# -------------------------------------------------
# PDF GENERATOR (RAW BYTES ONLY)
# -------------------------------------------------
def generate_cv_pdf_bytes(cv) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Name",
        fontSize=18,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="Section",
        fontSize=11,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="Body",
        fontSize=10
    ))

    story = [
        Paragraph(cv["name"], styles["Name"]),
        Paragraph(cv["title"], styles["Body"]),
        Paragraph(
            f'{cv["location"]} | {cv["phone"]} | {cv["email"]} | {cv["linkedin"]}',
            styles["Body"]
        ),
        HRFlowable(width="100%", thickness=1),
        Spacer(1, 10),
    ]

    def section(title, content):
        if not content.strip():
            return
        story.append(Paragraph(title.upper(), styles["Section"]))
        for line in content.split("\n"):
            if line.startswith("-"):
                story.append(ListFlowable(
                    [ListItem(Paragraph(line[1:], styles["Body"]))],
                    bulletType="bullet"
                ))
            else:
                story.append(Paragraph(line, styles["Body"]))

    section("Education", cv["education"])
    section("Experience", cv["experience"])
    section("Projects", cv["projects"])
    section("Skills", cv["skills"])

    doc.build(story)
    return buffer.getvalue()


# -------------------------------------------------
# STREAMLIT APP
# -------------------------------------------------
def main():
    st.title("AI CV Generator")

    # --- State init ---
    for k in [
        "name", "title", "location", "phone", "email", "linkedin",
        "education", "experience", "projects", "skills",
        "cv_ready", "eval_md", "want_download"
    ]:
        st.session_state.setdefault(k, "")

    if "want_download" not in st.session_state:
        st.session_state.want_download = False

    # --- Inputs ---
    st.text_input("Full Name", key="name")
    st.text_input("Professional Title", key="title")
    st.text_input("Location", key="location")
    st.text_input("Phone", key="phone")
    st.text_input("Email", key="email")
    st.text_input("LinkedIn", key="linkedin")
    st.text_area("Education", key="education")
    st.text_area("Experience", key="experience")
    st.text_area("Projects (optional)", key="projects")
    st.text_area("Skills", key="skills")

    # --- Generate ---
    if st.button("Generate CV"):
        cv = build_cv_data()
        _, st.session_state.eval_md = generate_cv_and_evaluation(
            {
                "name": cv["name"],
                "experience": cv["experience"],
                "education": cv["education"],
                "skills": cv["skills"].split(","),
                "job_description": ""
            },
            ""
        )
        st.session_state.cv_ready = True
        st.session_state.want_download = False

    # --- Actions ---
    if st.session_state.cv_ready:
        cv = build_cv_data()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👁 View CV (HTML – New Tab)"):
                open_html_new_tab(cv)

        with col2:
            if st.button("⬇ Download CV (PDF)"):
                st.session_state.want_download = True

        # --- Actual download (only after explicit intent) ---
        if st.session_state.want_download:
            st.download_button(
                label="Click here to save PDF",
                data=generate_cv_pdf_bytes(cv),
                file_name=safe_filename(cv["name"]),
                mime="application/pdf"
            )
            # reset to prevent rerun auto-download
            st.session_state.want_download = False

        st.subheader("Career Match Evaluation")
        st.markdown(st.session_state.eval_md)


if __name__ == "__main__":
    main()
