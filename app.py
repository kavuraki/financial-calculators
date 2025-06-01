import streamlit as st

# Set the page configuration
st.set_page_config(
    page_title="Financial Calculation Tools",
    layout="wide"
)

# Main title for the application
st.title("Financial Calculation Tools")

# Header for the dashboard
st.header("Calculator Dashboard")

st.markdown("Welcome to the Financial Calculation Tools application. Select a calculator from the sidebar to get started.")
st.markdown("---")

# Placeholder for links - Streamlit handles navigation via the 'pages' directory.
# We will add some descriptive text or visual cues if needed.

st.subheader("Available Calculators:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### [Compound Interest Calculator](Compound_Interest)")
    st.caption("Calculate the future value of your investment with compound interest.")

with col2:
    st.markdown("### [Loan Payment Calculator](Loan_Payment)")
    st.caption("Estimate your monthly loan payments.")

with col3:
    st.markdown("### [Retirement Savings Calculator](Retirement_Savings)")
    st.caption("Plan your retirement savings goals.")

st.markdown("---")
st.markdown("Navigate to the desired calculator using the sidebar on the left.")
