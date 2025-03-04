import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .stApp {
            font-family: 'Arial', sans-serif;
        }
        .main-header {
            color: #4a90e2;
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        .loan-card {
            background-color: #2d2d2d;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            border: 1px solid #4a90e2;
        }
        .status-paid {
            color: #00ff00;
            font-weight: bold;
        }
        .status-unpaid {
            color: #ff4444;
            font-weight: bold;
        }
        .donation-amount {
            color: #4CAF50;  /* Readable green color */
            font-weight: bold;
        }
        .expense-amount {
            color: #F44336;  /* Readable red color */
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)