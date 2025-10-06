# AI-PYTHON-RECRUITER
The Automated Technical Recruiter: Dynamic Python Screening Pipeline
This project is a sophisticated, full-stack Python application designed to modernize the initial candidate screening process. It transforms raw resume data into a personalized, scored technical interview, ensuring efficiency and objectivity in hiring.

Problem Solved
Traditional résumé screening and fixed interview scripts are time-consuming and often fail to accurately gauge a candidate's actual skill level before an expensive human interview. This application solves that by automating the filtering and tailoring the technical assessment.

Key Features and Architecture
The pipeline operates in three distinct stages:

Resume Ingestion & Ranking (NLP Simulation):

Function: Accepts multiple PDF/TXT resumes via a Streamlit file uploader.

Analysis: Uses PyPDF2 and custom Weighted Keyword Scoring (simulating an LLM/NLP engine) to analyze skills, experience, and education.

Output: Assigns each candidate a Seniority Tier (Junior, Mid-Level, or Senior) and a composite Score, displayed in a sortable Pandas DataFrame.

Dynamic Interview Generation:

Personalization: The core RecruiterBot class uses the candidate's assigned Tier Rank to dynamically select a unique set of 10 questions from a master roster of 20. (e.g., Senior candidates receive more Advanced questions on topics like Decorators and System Architecture).

Time Enforcement: Enforces a strict 20-minute limit using the Python time module.

Objective Assessment & Reporting:

The bot conducts the full, interactive interview via the chat interface.

All scoring is based on objective keyword matching.

After the interview, it generates a detailed Performance Analysis Breakdown, including total score, technical vs. generic performance, and a comparison against the model answer key.

Technologies Used
Category	Tools
Frontend/Deployment	Streamlit (Full Web App Framework, UI/UX)
Backend/Core Logic	Python (OOP Classes), time, random
Data/Analysis	Pandas (for tabular ranking), PyPDF2 (for file ingestion
