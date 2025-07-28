#!/usr/bin/env python3
"""
CTC Breakup Calculator - Streamlit Cloud Version
Professional salary breakdown calculator for Indian companies
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import json
from datetime import datetime

# =====================================================
# CONFIGURATION & DEFAULTS
# =====================================================

# Default percentage values for CTC components
DEFAULT_PERCENTAGES = {
    'basic': 40.0,          # 40% of CTC
    'pf': 12.0,             # 12% of Basic
    'gratuity': 4.81,       # 4.81% of Basic
    'bonus': 10.0,          # 10% of CTC
    'lta': 5.0,             # 5% of CTC
}

# HRA rates based on city type
METRO_HRA_RATE = 0.50       # 50% of Basic for Metro cities
NON_METRO_HRA_RATE = 0.40   # 40% of Basic for Non-Metro cities

# Validation limits
MIN_CTC = 10000         # Minimum CTC in rupees
MAX_CTC = 100000000     # Maximum CTC in rupees (10 crores)

# Component limits (as percentages)
COMPONENT_LIMITS = {
    'basic': {'min': 30.0, 'max': 60.0},
    'hra': {'min': 20.0, 'max': 60.0},    # as % of basic
    'pf': {'min': 8.0, 'max': 15.0},
    'gratuity': {'min': 3.0, 'max': 6.0},
    'bonus': {'min': 0.0, 'max': 20.0},
    'lta': {'min': 0.0, 'max': 10.0},
}

# Metro cities list
METRO_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Kolkata', 'Chennai', 'Hyderabad',
    'Pune', 'Ahmedabad', 'Surat', 'Kanpur', 'Jaipur', 'Lucknow',
    'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad'
]

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def calculate_ctc_breakup(ctc_amount, city_type, basic_percent=None, hra_percent=None,
                         pf_percent=None, gratuity_percent=None, bonus_percent=None, lta_percent=None):
    """Calculate detailed CTC breakup"""

    # Use defaults if not provided
    basic_percent = basic_percent or DEFAULT_PERCENTAGES['basic']
    pf_percent = pf_percent or DEFAULT_PERCENTAGES['pf']
    gratuity_percent = gratuity_percent or DEFAULT_PERCENTAGES['gratuity']
    bonus_percent = bonus_percent or DEFAULT_PERCENTAGES['bonus']
    lta_percent = lta_percent or DEFAULT_PERCENTAGES['lta']

    # Calculate HRA rate based on city type if not provided
    if hra_percent is None:
        hra_rate = METRO_HRA_RATE if city_type == "Metro" else NON_METRO_HRA_RATE
    else:
        hra_rate = hra_percent

    # Calculate components
    basic_amount = ctc_amount * (basic_percent / 100)
    hra_amount = basic_amount * hra_rate
    pf_amount = basic_amount * (pf_percent / 100)
    gratuity_amount = basic_amount * (gratuity_percent / 100)
    bonus_amount = ctc_amount * (bonus_percent / 100)
    lta_amount = ctc_amount * (lta_percent / 100)

    # Calculate special allowance (balancing figure)
    total_fixed = basic_amount + hra_amount + pf_amount + gratuity_amount + bonus_amount + lta_amount
    special_allowance = max(0, ctc_amount - total_fixed)

    # Create breakup dictionary
    breakup = {
        'Basic Salary': {
            'amount': round(basic_amount, 2),
            'percentage': round((basic_amount / ctc_amount) * 100, 2)
        },
        'HRA': {
            'amount': round(hra_amount, 2),
            'percentage': round((hra_amount / ctc_amount) * 100, 2)
        },
        'Special Allowance': {
            'amount': round(special_allowance, 2),
            'percentage': round((special_allowance / ctc_amount) * 100, 2)
        },
        'Employer PF': {
            'amount': round(pf_amount, 2),
            'percentage': round((pf_amount / ctc_amount) * 100, 2)
        },
        'Gratuity': {
            'amount': round(gratuity_amount, 2),
            'percentage': round((gratuity_amount / ctc_amount) * 100, 2)
        },
        'Bonus/Variable': {
            'amount': round(bonus_amount, 2),
            'percentage': round((bonus_amount / ctc_amount) * 100, 2)
        },
        'LTA/Other Benefits': {
            'amount': round(lta_amount, 2),
            'percentage': round((lta_amount / ctc_amount) * 100, 2)
        }
    }

    return breakup

def validate_inputs(ctc_amount, basic_percent, pf_percent, gratuity_percent, bonus_percent, lta_percent):
    """Validate input parameters"""
    errors = []

    # CTC validation
    if ctc_amount <= 0:
        errors.append("CTC amount must be greater than 0")
    elif ctc_amount < MIN_CTC:
        errors.append(f"CTC amount seems too low (minimum ₹{MIN_CTC:,})")
    elif ctc_amount > MAX_CTC:
        errors.append(f"CTC amount seems too high (maximum ₹{MAX_CTC:,})")

    # Percentage validations
    if basic_percent <= 0 or basic_percent > 100:
        errors.append("Basic salary percentage must be between 0-100%")

    if pf_percent < 0 or pf_percent > 100:
        errors.append("PF percentage must be between 0-100%")

    if gratuity_percent < 0 or gratuity_percent > 100:
        errors.append("Gratuity percentage must be between 0-100%")

    if bonus_percent < 0 or bonus_percent > 100:
        errors.append("Bonus percentage must be between 0-100%")

    if lta_percent < 0 or lta_percent > 100:
        errors.append("LTA percentage must be between 0-100%")

    # Total percentage check
    total_percent = basic_percent + pf_percent + gratuity_percent + bonus_percent + lta_percent
    if total_percent > 120:
        errors.append(f"Total percentages exceed reasonable limits ({total_percent:.1f}%)")

    # Logical validations
    if pf_percent > basic_percent:
        errors.append("PF percentage cannot exceed Basic salary percentage")

    if gratuity_percent > basic_percent:
        errors.append("Gratuity percentage cannot exceed Basic salary percentage")

    return errors

def format_currency(amount):
    """Format amount as Indian currency"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.0f}"

def create_pdf_report(breakup_data, ctc_amount, city_type):
    """Generate PDF report of CTC breakup"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)

        # Title
        pdf.cell(200, 10, txt="CTC Breakup Report", ln=1, align='C')
        pdf.ln(10)

        # Basic info
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Total CTC: {format_currency(ctc_amount)}", ln=1)
        pdf.cell(200, 10, txt=f"City Type: {city_type}", ln=1)
        pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
        pdf.ln(10)

        # Table header
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(80, 10, txt="Component", border=1)
        pdf.cell(40, 10, txt="Amount (₹)", border=1)
        pdf.cell(30, 10, txt="Percentage", border=1)
        pdf.ln()

        # Table data
        pdf.set_font("Arial", size=10)
        for component, data in breakup_data.items():
            pdf.cell(80, 8, txt=component, border=1)
            pdf.cell(40, 8, txt=f"{data['amount']:,.0f}", border=1)
            pdf.cell(30, 8, txt=f"{data['percentage']:.2f}%", border=1)
            pdf.ln()

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        # Fallback to text report if PDF fails
        content = f"""
CTC BREAKUP REPORT
==================

Total CTC: {format_currency(ctc_amount)}
City Type: {city_type}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Component Breakdown:
-------------------
"""
        for component, data in breakup_data.items():
            content += f"{component:<25}: ₹{data['amount']:>12,.0f} ({data['percentage']:>6.2f}%)\n"
        
        return content.encode('utf-8')

# =====================================================
# STREAMLIT APPLICATION
# =====================================================

# Page configuration
st.set_page_config(
    page_title="CTC Breakup Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    defaults = {
        'ctc_amount': 1000000.0,
        'city_type': "Metro",
        'basic_percent': DEFAULT_PERCENTAGES['basic'],
        'hra_percent': None,
        'pf_percent': DEFAULT_PERCENTAGES['pf'],
        'gratuity_percent': DEFAULT_PERCENTAGES['gratuity'],
        'bonus_percent': DEFAULT_PERCENTAGES['bonus'],
        'lta_percent': DEFAULT_PERCENTAGES['lta'],
        'dark_mode': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def main():
    initialize_session_state()

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
    }
    .results-table {
        border: 1px solid #ddd;
        border-radius: 10px;
        overflow: hidden;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
   .streamlit-info {
    background: #263238; /* blue-gray background */
    border-left: 4px solid #00acc1;  /* cyan accent */
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 5px;
    color: #e0f7fa;  /* Light text for readability */
}
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>💰 CTC Breakup Calculator</h1>
        <p>Calculate detailed Cost to Company breakdown with Indian salary standards</p>
        <small>🌟 Hosted on Streamlit Cloud - Always Available</small>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit Cloud information banner
    st.markdown("""
    <div class="streamlit-info">
        <h4>🌟  Online CTC Calculator!</h4>
        <p>✅ Easier calculation of pesky salaries <br>
        📱 Share this URL with anyone<br>
        💾 Download reports anytime<br>
        🔄 Now know exacly what 30 LPA means </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for inputs
    with st.sidebar:
        st.header("📊 Input Parameters")

        # Dark mode toggle
        st.session_state.dark_mode = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode)

        st.divider()

        # CTC Input
        st.subheader("💵 CTC Details")

        input_type = st.radio("Input Format:", ["LPA (Lakhs Per Annum)", "Absolute Amount (₹)"])

        if input_type == "LPA (Lakhs Per Annum)":
            lpa_value = st.number_input("CTC in LPA:", min_value=0.1, max_value=1000.0,
                                       value=st.session_state.ctc_amount/100000, step=0.1)
            st.session_state.ctc_amount = lpa_value * 100000
        else:
            st.session_state.ctc_amount = st.number_input("CTC Amount (₹):", min_value=10000.0,
                                                         max_value=100000000.0,
                                                         value=st.session_state.ctc_amount, step=1000.0)

        st.session_state.city_type = st.selectbox("City Type:", ["Metro", "Non-Metro"],
                                                  index=0 if st.session_state.city_type == "Metro" else 1)

        st.divider()

        # Component Percentages
        st.subheader("📈 Component Percentages")

        use_defaults = st.checkbox("Use Default Percentages", value=True)

        if not use_defaults:
            st.session_state.basic_percent = st.slider("Basic Salary %:", 30.0, 60.0,
                                                       st.session_state.basic_percent, 0.1)

            # HRA calculation based on city type
            default_hra = METRO_HRA_RATE if st.session_state.city_type == "Metro" else NON_METRO_HRA_RATE
            hra_of_basic = st.slider("HRA (% of Basic):", 20.0, 60.0, default_hra*100, 0.1)
            st.session_state.hra_percent = hra_of_basic / 100

            st.session_state.pf_percent = st.slider("Employer PF %:", 8.0, 15.0,
                                                    st.session_state.pf_percent, 0.1)
            st.session_state.gratuity_percent = st.slider("Gratuity %:", 3.0, 6.0,
                                                          st.session_state.gratuity_percent, 0.01)
            st.session_state.bonus_percent = st.slider("Bonus/Variable %:", 0.0, 20.0,
                                                       st.session_state.bonus_percent, 0.1)
            st.session_state.lta_percent = st.slider("LTA/Other Benefits %:", 0.0, 10.0,
                                                     st.session_state.lta_percent, 0.1)
        else:
            # Reset to defaults
            st.session_state.basic_percent = DEFAULT_PERCENTAGES['basic']
            st.session_state.hra_percent = None
            st.session_state.pf_percent = DEFAULT_PERCENTAGES['pf']
            st.session_state.gratuity_percent = DEFAULT_PERCENTAGES['gratuity']
            st.session_state.bonus_percent = DEFAULT_PERCENTAGES['bonus']
            st.session_state.lta_percent = DEFAULT_PERCENTAGES['lta']

        # Reset button
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            for key in ['ctc_amount', 'city_type', 'basic_percent', 'hra_percent',
                       'pf_percent', 'gratuity_percent', 'bonus_percent', 'lta_percent']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # Quick preset buttons
        st.subheader("⚡ Quick Presets")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👨‍💼 Standard", use_container_width=True):
                st.session_state.ctc_amount = 1000000
                st.session_state.city_type = "Metro"
                st.rerun()

        with col2:
            if st.button("🚀 Senior", use_container_width=True):
                st.session_state.ctc_amount = 2000000
                st.session_state.city_type = "Metro"
                st.rerun()

        # Additional presets
        st.subheader("💼 More Presets")
        
        preset_col1, preset_col2 = st.columns(2)
        with preset_col1:
            if st.button("🎓 Entry Level", use_container_width=True):
                st.session_state.ctc_amount = 500000
                st.session_state.city_type = "Non-Metro"
                st.rerun()

        with preset_col2:
            if st.button("💎 Executive", use_container_width=True):
                st.session_state.ctc_amount = 3000000
                st.session_state.city_type = "Metro"
                st.rerun()

        # App info
        st.divider()
        st.markdown("### 📱 Share This App")
        st.info("""
        **Features:**
        • Always online (24/7)
        • Real-time calculations
        • Export to PDF/CSV/JSON
        • Mobile-friendly design
        • Professional reports
        """)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Input validation
        validation_errors = validate_inputs(
            st.session_state.ctc_amount,
            st.session_state.basic_percent,
            st.session_state.pf_percent,
            st.session_state.gratuity_percent,
            st.session_state.bonus_percent,
            st.session_state.lta_percent
        )

        if validation_errors:
            st.error("⚠️ Input Validation Errors:")
            for error in validation_errors:
                st.error(f"• {error}")
        else:
            # Calculate breakup
            breakup = calculate_ctc_breakup(
                st.session_state.ctc_amount,
                st.session_state.city_type,
                st.session_state.basic_percent,
                st.session_state.hra_percent,
                st.session_state.pf_percent,
                st.session_state.gratuity_percent,
                st.session_state.bonus_percent,
                st.session_state.lta_percent
            )

            # Results table
            st.subheader("📋 CTC Breakup Results")

            # Create styled DataFrame
            df_data = []
            for component, data in breakup.items():
                df_data.append({
                    'Component': component,
                    'Amount (₹)': f"₹{data['amount']:,.0f}",
                    'Percentage (%)': f"{data['percentage']:.2f}%",
                    'Monthly (₹)': f"₹{data['amount']/12:,.0f}"
                })

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Summary metrics
            st.subheader("📊 Key Metrics")

            basic_amount = breakup['Basic Salary']['amount']
            hra_amount = breakup['HRA']['amount']
            take_home = basic_amount + hra_amount + breakup['Special Allowance']['amount']

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric("💰 Basic Salary", format_currency(basic_amount),
                         f"₹{basic_amount/12:,.0f}/month")
            with metric_col2:
                st.metric("🏠 HRA", format_currency(hra_amount),
                         f"₹{hra_amount/12:,.0f}/month")
            with metric_col3:
                st.metric("💸 Approx. Take Home", format_currency(take_home),
                         f"₹{take_home/12:,.0f}/month")
            with metric_col4:
                st.metric("📈 Total CTC", format_currency(st.session_state.ctc_amount),
                         f"₹{st.session_state.ctc_amount/12:,.0f}/month")

            # Additional insights
            st.subheader("🔍 Salary Insights")

            insight_col1, insight_col2 = st.columns(2)

            with insight_col1:
                # Tax implications
                if st.session_state.ctc_amount >= 1000000:
                    tax_bracket = "30% tax bracket"
                elif st.session_state.ctc_amount >= 500000:
                    tax_bracket = "20% tax bracket"
                else:
                    tax_bracket = "5% tax bracket"

                st.info(f"💼 **Tax Bracket**: {tax_bracket}")

                # PF analysis
                pf_employee = breakup['Employer PF']['amount']
                st.info(f"🏦 **Employee PF**: ₹{pf_employee:,.0f} (deducted from salary)")

            with insight_col2:
                # City comparison
                if st.session_state.city_type == "Metro":
                    st.success("🏙️ **Metro City**: Higher HRA (50% of Basic)")
                else:
                    st.warning("🌆 **Non-Metro**: Lower HRA (40% of Basic)")

                # Special allowance analysis
                special_pct = breakup['Special Allowance']['percentage']
                if special_pct > 30:
                    st.warning(f"⚠️ **High Special Allowance**: {special_pct:.1f}% - Consider rebalancing")
                else:
                    st.success(f"✅ **Balanced Structure**: {special_pct:.1f}% Special Allowance")

    with col2:
        st.subheader("📥 Download & Export")

        if not validation_errors:
            # CSV Download
            csv_data = pd.DataFrame([(k, v['amount'], v['percentage']) for k, v in breakup.items()],
                                   columns=['Component', 'Amount', 'Percentage'])
            csv_buffer = BytesIO()
            csv_data.to_csv(csv_buffer, index=False)

            st.download_button(
                label="📄 Download CSV Report",
                data=csv_buffer.getvalue(),
                file_name=f"ctc_breakup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            # PDF Download
            pdf_data = create_pdf_report(breakup, st.session_state.ctc_amount, st.session_state.city_type)

            if pdf_data:
                st.download_button(
                    label="📑 Download PDF Report",
                    data=pdf_data,
                    file_name=f"ctc_breakup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            # JSON Export
            json_data = json.dumps({
                'ctc_amount': st.session_state.ctc_amount,
                'city_type': st.session_state.city_type,
                'breakup': breakup,
                'generated_at': datetime.now().isoformat()
            }, indent=2)

            st.download_button(
                label="📋 Download JSON Data",
                data=json_data,
                file_name=f"ctc_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        else:
            st.info("🔧 Fix validation errors to enable downloads")

        # Calculation summary
        st.subheader("🧮 Current Settings")
        st.write(f"**CTC**: {format_currency(st.session_state.ctc_amount)}")
        st.write(f"**City**: {st.session_state.city_type}")
        st.write(f"**Basic**: {st.session_state.basic_percent}%")
        st.write(f"**PF**: {st.session_state.pf_percent}%")
        st.write(f"**Bonus**: {st.session_state.bonus_percent}%")

        # Sample calculations for different CTCs
        st.subheader("📊 Quick Comparisons")

        sample_ctcs = [300000, 500000, 800000, 1000000, 1500000, 2000000]

        for sample_ctc in sample_ctcs:
            if st.button(f"Calculate for {format_currency(sample_ctc)}", 
                        key=f"sample_{sample_ctc}", use_container_width=True):
                st.session_state.ctc_amount = sample_ctc
                st.rerun()

    # Formulas and explanations
    with st.expander("📐 Calculation Formulas & Methodology"):
        st.markdown("""
        ### 🧮 Calculation Formulas

        **Basic Components:**
        - **Basic Salary** = CTC × Basic %
        - **HRA** = Basic Salary × HRA Rate
          - 🏙️ Metro: 50% of Basic
          - 🌆 Non-Metro: 40% of Basic

        **Statutory Components:**
        - **Employer PF** = Basic Salary × 12%
        - **Gratuity** = Basic Salary × 4.81%

        **Benefits & Allowances:**
        - **Bonus/Variable** = CTC × Bonus %
        - **LTA/Other Benefits** = CTC × LTA %

        **Balancing Figure:**
        - **Special Allowance** = CTC - (Sum of all other components)

        ### 📋 Important Notes:

        1. **HRA Calculation**: Based on city classification (Metro vs Non-Metro)
        2. **PF & Gratuity**: Always calculated on Basic Salary
        3. **Special Allowance**: Automatically balances to make total = CTC
        4. **Tax Implications**: Higher Special Allowance = Higher tax burden
        5. **Take-Home Estimate**: Excludes employee PF, professional tax, and income tax

        ### 🎯 Optimization Tips:

        - **Increase Basic**: Higher PF contribution, better retirement corpus
        - **Optimize HRA**: Claim house rent allowance for tax benefits
        - **Balance Special Allowance**: Keep under 30% for better tax efficiency
        - **Utilize Benefits**: LTA and other allowances have tax advantages
        """)

    # Footer with additional information
    st.divider()

    footer_col1, footer_col2, footer_col3 = st.columns(3)

    with footer_col1:
        st.markdown("""
        **🔧 Built with:**
        - Streamlit for UI
        - Python for calculations
        - Pandas for data handling
        - FPDF2 for PDF reports
        """)

    with footer_col2:
        st.markdown("""
        **📊 Features:**
        - Real-time calculations
        - Export to CSV/PDF/JSON
        - Mobile-friendly design
        - Always online (24/7)
        """)

    with footer_col3:
        st.markdown("""
        **🇮🇳 Indian Standards:**
        - PF regulations compliant
        - Metro/Non-Metro HRA rates
        - Statutory benefits included
        """)

    st.markdown("---")
    st.markdown("Made with ❤️ for Indian professionals by DANUSH VIKRAMAN SB | Version 2.1 | 🌟 Hosted on Streamlit Cloud")

    # Usage analytics (optional)
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        💡 Tip: Bookmark this page for quick access to CTC calculations anytime!
    </div>
    """, unsafe_allow_html=True)

# Run the main app
if __name__ == "__main__":
    main()