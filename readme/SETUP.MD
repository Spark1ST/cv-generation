# Setup Guide for AI CV Generator with Career Matching

## Prerequisites

Before you begin, make sure you have the following software installed:
- Python 3.8 or later
- pip (Python package installer)
- Git (optional, if you are cloning the repository)

## 1. Clone the Repository

Clone the repository to your local machine:

bash

git clone <repository_url>
cd <repository_directory>

2. Install Dependencies
Create a virtual environment (optional but recommended):

bash

python -m venv venv
source venv/bin/activate  # For macOS/Linux
venv\Scripts\activate     # For Windows

Install required packages:

bash
pip install -r requirements.txt
3. Set Up Environment Variables
Copy the config/key.env.example to config/key.env:

bash
cp config/key.env.example config/key.env
Edit the config/key.env file to include your API keys and other sensitive credentials:

bash
GOOGLE_API_KEY=your_google_api_key
AGENTOPS_API_KEY=your_agentops_api_key
You can obtain the GOOGLE_API_KEY from the Google Cloud Platform and the AGENTOPS_API_KEY from AgentOps.

4. Run the Application
Once the setup is complete, you can run the application using:

bash
streamlit run pages/form.py
This will launch the Streamlit app in your default web browser.