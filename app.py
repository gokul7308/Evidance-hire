import streamlit as st
import os

from backend.config import Config
from backend.database.db import init_db

def main():
    st.set_page_config(page_title="EvidenceHire", page_icon="📄", layout="wide")
    
    st.title("EvidenceHire")
    st.subheader("Hallucination-Safe, Duplicate-Aware Resume Screening Agent")
    
    # Initialize the database on startup
    init_db()
    
    st.info("System is ready. Awaiting further implementation...")

if __name__ == "__main__":
    main()
