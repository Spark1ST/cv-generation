# form.py

import streamlit as st
import json
import sys
import os

# Add the root directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cv_generator import generate_cv_and_evaluation, read_file_or_warn

# Streamlit App

def main():
    st.title("AI CV Generator with Career Matching")

    # — Session state flags —
    if "running" not in st.session_state:
        st.session_state.running = False
    if "done" not in st.session_state:
        st.session_state.done = False
    if "cv_md" not in st.session_state:
        st.session_state.cv_md = None
    if "eval_md" not in st.session_state:
        st.session_state.eval_md = None

    # — User inputs —
    # Minimum character requirements (adjust as needed)
    MIN_LENGTHS = {
        "name": 2,
        "experience": 20,
        "education": 15,
        "skills": 3,
        "job_desc": 20,
    }

    name       = st.text_input("Full Name")
    experience = st.text_area("Professional Experience")
    education  = st.text_area("Education History")
    skills     = st.text_input("Skills / Certificates (comma-separated)")
    job_desc   = st.text_area("Target Job Description")

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

    inputs_valid= len(invalid_fields)

    # — on_click callback to kick off generation —
    def start_generation():
  
        if invalid_fields:
            for field, have, need in invalid_fields:
                st.warning(f"'{field}' is too short: {have} chars (min {need})")

        inputs_valid = len(invalid_fields) == 0
        if inputs_valid:
            st.session_state.running = True
            st.session_state.done = False

    # — Generate button, disabled while running —
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
                "skills": [s.strip() for s in skills.split(",")],
                "job_description": job_desc
            }
            cv_md, eval_md = generate_cv_and_evaluation(user_data, job_desc)

        # stash results and clear running
        st.session_state.cv_md = cv_md
        st.session_state.eval_md = eval_md
        st.session_state.running = False
        st.session_state.done = True

    # — Once done, show results —
    if st.session_state.done:
        
        st.subheader("Your Professional CV")
        if st.session_state.cv_md:
            st.markdown(st.session_state.cv_md)
        else:
            st.info("CV content not available.")

        st.subheader("Career Match Evaluation")
        if st.session_state.eval_md:
            st.markdown(st.session_state.eval_md)
        else:
            st.info("No evaluation results available.")
            
if __name__ == "__main__":
    main()