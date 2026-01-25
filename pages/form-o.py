# form.py
import streamlit as st
import json
import sys
import os
import re
import base64
import html
import io

# Add the root directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cv_generator import generate_cv_and_evaluation, read_file_or_warn

import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# -------------------------
# Helpers
# -------------------------
def extract_match_score(eval_md, user_skills, job_desc):
    # Try to find a percentage in the evaluation text
    if eval_md:
        m = re.search(r'(\d{1,3})\s*%', eval_md)
        if m:
            try:
                val = int(m.group(1))
                return max(0, min(100, val))
            except:
                pass
    # Fallback heuristic: percent of skills that appear in JD
    try:
        skills = [s.strip().lower() for s in user_skills if s and s.strip()]
        if len(skills) == 0:
            return 0
        jd = (job_desc or "").lower()
        hits = sum(1 for s in skills if s and s in jd)
        score = int((hits / len(skills)) * 100)
        return max(0, min(100, score))
    except:
        return 0

def make_pie_png_bytes(match_score, size_px=300, dpi=150):
    """
    Returns PNG bytes of the pie chart at high DPI so it's crisp.
    size_px controls the final pixel size (approx). DPI controls sharpness.
    """
    non_match = 100 - match_score
    # Convert size_px and dpi to inches for figsize
    inches = size_px / dpi
    fig, ax = plt.subplots(figsize=(inches, inches), dpi=dpi)
    wedges, texts = ax.pie(
        [match_score, non_match],
        labels=[f"Match\n{match_score}%", f"Gap\n{non_match}%"],
        startangle=90,
        wedgeprops=dict(width=0.5, edgecolor="w"),
        textprops={"fontsize": 10}
    )
    ax.set(aspect="equal")
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def build_cv_html(cv_md, title="Generated CV"):
    # convert markdown to escaped HTML inside a simple container but keep nice fonts
    safe_md = html.escape(cv_md or "")
    html_page = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>{html.escape(title)}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <style>
      body{{font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; padding:24px; line-height:1.5; background:#f7f7f8; color:#111;}}
      .card{{background:#fff; border:1px solid #e1e4e8; padding:22px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.04); max-width:900px; margin:auto}}
      pre{{white-space:pre-wrap; word-wrap:break-word; font-family:inherit; font-size:14px;}}
      h1{{font-size:20px; margin-bottom:6px}}
      @media (max-width:600px) {{ body {{ padding:12px }} .card {{ padding:14px }} }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>{html.escape(title)}</h1>
      <pre>{safe_md}</pre>
    </div>
  </body>
</html>"""
    return html_page

# -------------------------
# Streamlit app
# -------------------------
def main():
    st.set_page_config(page_title="AI CV Generator", layout="centered")
    st.title("AI CV Generator with Career Matching")

    # Initialize session_state storage for results and profiles
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("done", False)
    st.session_state.setdefault("cv_md", None)
    st.session_state.setdefault("eval_md", None)
    st.session_state.setdefault("profiles", {})  # name -> dict of fields

    # Sidebar: Profiles (save/load/delete)
    st.sidebar.header("Profiles / Presets")
    profiles = st.session_state["profiles"]
    profile_names = list(profiles.keys())
    selected_profile = st.sidebar.selectbox("Load profile", options=["(none)"] + profile_names)

    if selected_profile != "(none)":
        if st.sidebar.button("Apply selected profile"):
            prof = profiles[selected_profile]
            # populate UI by storing temp values in session_state so input widgets pick them up
            st.session_state["_prefill_name"] = prof.get("name", "")
            st.session_state["_prefill_experience"] = prof.get("experience", "")
            st.session_state["_prefill_education"] = prof.get("education", "")
            st.session_state["_prefill_skills"] = ", ".join(prof.get("skills", []))
            st.session_state["_prefill_job_desc"] = prof.get("job_description", "")

    new_profile_name = st.sidebar.text_input("Save current as profile (name)")
    if st.sidebar.button("Save profile") and new_profile_name.strip():
        # capture current entries (if exist)
        profiles[new_profile_name.strip()] = {
            "name": st.session_state.get("_last_inputs_name", "") ,
            "experience": st.session_state.get("_last_inputs_experience", ""),
            "education": st.session_state.get("_last_inputs_education", ""),
            "skills": st.session_state.get("_last_inputs_skills_list", []),
            "job_description": st.session_state.get("_last_inputs_job_desc", "")
        }
        st.sidebar.success(f"Saved profile '{new_profile_name.strip()}'")

    if selected_profile != "(none)" and st.sidebar.button("Delete profile"):
        profiles.pop(selected_profile, None)
        st.sidebar.success(f"Deleted '{selected_profile}'")

    # Provide a quick sample preset for convenience
    if st.sidebar.button("Load sample profile"):
        st.session_state["_prefill_name"] = "Mohammed Mahmoud Hamad"
        st.session_state["_prefill_experience"] = "AI Engineer at XYZ — developed CV generator, RAG pipelines, model deployment with FastAPI and Streamlit. Focused on LLM and CV projects."
        st.session_state["_prefill_education"] = "BSc Computer Science — Ain Shams University"
        st.session_state["_prefill_skills"] = "PyTorch, TensorFlow, FastAPI, Streamlit, Docker, Hugging Face"
        st.session_state["_prefill_job_desc"] = "AI/ML Engineer role focusing on model deployment, PyTorch, and computer vision."

    # — User inputs —
    MIN_LENGTHS = {
        "name": 2,
        "experience": 20,
        "education": 15,
        "skills": 3,
        "job_desc": 6,
    }

    # If prefill values exist in session_state, use them as default values for inputs
    name = st.text_input("Full Name", value=st.session_state.pop("_prefill_name", None) or "")
    experience = st.text_area("Professional Experience", value=st.session_state.pop("_prefill_experience", "") or "")
    education = st.text_area("Education History", value=st.session_state.pop("_prefill_education", "") or "")
    skills = st.text_input("Skills / Certificates (comma-separated)", value=st.session_state.pop("_prefill_skills", "") or "")
    job_desc = st.text_area("Target Job Description", value=st.session_state.pop("_prefill_job_desc", "") or "")

    # Keep last inputs cached for saving profiles
    st.session_state["_last_inputs_name"] = name
    st.session_state["_last_inputs_experience"] = experience
    st.session_state["_last_inputs_education"] = education
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    st.session_state["_last_inputs_skills_list"] = skills_list
    st.session_state["_last_inputs_job_desc"] = job_desc

    # Validate minimum character lengths
    lengths = {
        "name": len(name.strip()),
        "experience": len(experience.strip()),
        "education": len(education.strip()),
        "skills": len(skills.strip()),
        "job_desc": len(job_desc.strip()),
    }

    invalid_fields = [
        (k, lengths[k], MIN_LENGTHS[k])
        for k in MIN_LENGTHS
        if lengths[k] < MIN_LENGTHS[k]
    ]
    inputs_valid = len(invalid_fields) == 0

    # — on_click callback to kick off generation —
    def start_generation():
        if invalid_fields:
            for field, have, need in invalid_fields:
                st.warning(f"'{field}' is too short: {have} chars (min {need})")
        if len(invalid_fields) == 0:
            st.session_state.running = True
            st.session_state.done = False

    # Generate button
    st.button(
        "Generate CV",
        on_click=start_generation,
        disabled=st.session_state.running or not inputs_valid
    )

    # — If running flag is set, immediately do the work with spinner —
    if st.session_state.running:
        with st.spinner("Generating your CV... Please wait!"):
            user_data = {
                "name": name,
                "experience": experience,
                "education": education,
                "skills": skills_list,
                "job_description": job_desc
            }
            cv_md, eval_md = generate_cv_and_evaluation(user_data, job_desc)

        st.session_state.cv_md = cv_md
        st.session_state.eval_md = eval_md
        st.session_state.running = False
        st.session_state.done = True

    # — Once done, show results —
    if st.session_state.done:
        st.subheader("Your Professional CV")
        if st.session_state.cv_md:
            # Show a short preview in the app
            st.markdown(st.session_state.cv_md)

            # Prepare an HTML page for the CV
            html_page = build_cv_html(st.session_state.cv_md, title=f"{name or 'Generated'} - CV")

            # Download button (HTML file)
            st.download_button(
                "Download CV (HTML)",
                data=html_page,
                file_name=f"{(name or 'cv').replace(' ','_')}.html",
                mime="text/html"
            )

            # JS blob-based new-tab opener (more reliable than raw data: URL anchors)
            b64 = base64.b64encode(html_page.encode("utf-8")).decode("utf-8")
            # Build a small JS widget that creates a blob from the base64 and opens in new tab
            js_widget = f"""
<div>
  <button id="opencv" style="padding:8px 12px">View CV (new tab)</button>
</div>
<script>
const b64 = "{b64}";
const str = atob(b64);
const uint8 = new TextEncoder().encode(str);
const blob = new Blob([uint8], {{ type: "text/html" }});
const url = URL.createObjectURL(blob);
document.getElementById("opencv").addEventListener("click", function() {{
    window.open(url, "_blank");
}});
</script>
"""
            components.html(js_widget, height=60)

        else:
            st.info("CV content not available.")

        # Evaluation area with a small crisp pie chart
        st.subheader("Career Match Evaluation")
        if st.session_state.eval_md:
            st.markdown(st.session_state.eval_md)

            match_score = extract_match_score(st.session_state.eval_md, skills_list, job_desc or "")
            png = make_pie_png_bytes(match_score, size_px=300, dpi=150)
            st.image(png, caption=f"Match: {match_score}%", use_column_width=False)
        else:
            st.info("No evaluation results available.")

if __name__ == "__main__":
    main()
