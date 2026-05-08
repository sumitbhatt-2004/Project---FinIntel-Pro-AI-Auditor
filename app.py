import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader
import json
import os

# --- 1. INITIALIZATION & ENHANCED UI STYLING ---
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


st.set_page_config(page_title="FinIntel Pro Auditor", layout="wide")

st.markdown("""
    <style>
    /* 1. Main Background - Clean Slate Grey */
    .stApp { 
        background: #f8fafc; 
        color: #1e293b; 
    }
    
    /* 2. Global Text - Soft Dark Blue-Grey */
    .stMarkdown, p, li { color: #334155 !important; font-family: 'Inter', sans-serif; }
    
    /* 3. Titles - Professional Emerald Green */
    h1, h2, h3 { color: #065f46 !important; font-weight: 700; }
    
    /* 4. Professional Tables - White with subtle borders */
    .stTable { 
        background-color: #ffffff; 
        border-radius: 8px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    thead tr th { 
        background-color: #f1f5f9 !important; 
        color: #0f172a !important; 
        border-bottom: 2px solid #059669 !important;
    }
    /* Fix for the dark cells you saw in your screenshot */
    [data-testid="stTable"] td {
        background-color: #ffffff !important;
        color: #1e293b !important;
    }

    /* 5. Chat Messages - "Slack-style" Clean Bubble */
    [data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    [data-testid="stChatMessage"] p { color: #1e293b !important; }

    /* 6. Narrative Cards - Subtle Green Accent */
    .insight-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border-top: 4px solid #10b981;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #1e293b !important;
    }

   /* 7. Sidebar - Deep Charcoal with High-Visibility Elements */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }

    /* Target labels and text for maximum clarity */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown p { 
        color: #ffffff !important; 
        font-weight: 500 !important;
    }

    /* Style the Sidebar Buttons (Reset/Clear) */
    [data-testid="stSidebar"] button {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
    }

    /* Interaction effect for buttons */
    [data-testid="stSidebar"] button:hover {
        border-color: #10b981 !important;
        color: #10b981 !important;
    }

    /* 8. Modern Input Box */
    .stChatInputContainer {
        background-color: #f8fafc !important;
        padding-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if "full_context" not in st.session_state:
    st.session_state.full_context = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. MULTI-DIMENSIONAL EXTRACTION ---
def get_comprehensive_audit(text):
    prompt = f"""
    You are a Senior Financial Auditor. Analyze the text and return ONLY a JSON object.
    Text: {text[:15000]}
    JSON structure:
    {{
        "p_l": {{ "Year": ["2025", "2026"], "Revenue": [0, 0], "Net_Income": [0, 0] }},
        "balance_sheet": {{ "Metric": ["Total Assets", "Total Liabilities", "Cash"], "Amount": [0, 0, 0] }},
        "cash_flow": {{ "Operating": 0, "Investing": 0, "Financing": 0 }},
        "analysis_report": "Provide a 4-paragraph detailed analysis of P&L, Balance Sheet, and Cash Flow trends."
    }}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- 3. MAIN APP INTERFACE ---
with st.sidebar:
    st.title("🛡️ Auditor Settings")
    uploaded_file = st.file_uploader("Upload Statement (PDF)", type="pdf")
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

st.title("📊 FinIntel Pro: Comprehensive Auditor")

if uploaded_file:
    temp_path = "temp_audit.pdf"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if not st.session_state.full_context:
        with st.spinner("Scanning all report sections..."):
            loader = PyPDFLoader(temp_path)
            pages = loader.load_and_split()
            important = [p.page_content for p in pages if any(k in p.page_content for k in ["Consolidated", "Operations", "Balance Sheet", "Cash Flow"])]
            st.session_state.full_context = " ".join(important[:8]) if important else " ".join([p.page_content for p in pages[:15]])

    tab_audit, tab_chat = st.tabs(["📑 Full Audit Dashboard", "💬 Ask the Auditor"])

    with tab_audit:
        if st.button("🔍 Generate Comprehensive Analysis"):
            with st.spinner("Crunching numbers..."):
                data = get_comprehensive_audit(st.session_state.full_context)
                st.subheader("Financial Statement Data")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Profit & Loss**")
                    st.table(pd.DataFrame(data['p_l']))
                with c2:
                    st.markdown("**Balance Sheet Snapshot**")
                    st.table(pd.DataFrame(data['balance_sheet']))

                st.divider()
                st.subheader("Visual Intelligence")
                v1, v2 = st.columns(2)
                with v1:
                    df_pl = pd.DataFrame(data['p_l'])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_pl['Year'], y=df_pl['Revenue'], name="Revenue", line=dict(color="#00df94")))
                    fig.add_trace(go.Bar(x=df_pl['Year'], y=df_pl['Net_Income'], name="Net Profit", marker_color="#636efa"))
                    st.plotly_chart(fig, use_container_width=True)
                with v2:
                    cf = data['cash_flow']
                    fig2 = go.Figure(go.Waterfall(
                        x = ["Operating", "Investing", "Financing"],
                        y = [cf['Operating'], cf['Investing'], cf['Financing']],
                        measure = ["relative", "relative", "relative"]
                    ))
                    fig2.update_layout(title="Cash Flow Breakdown")
                    st.plotly_chart(fig2, use_container_width=True)

                st.divider()
                st.subheader("📝 Auditor's Detailed Narrative")
                st.markdown(f'<div class="insight-card">{data.get("analysis_report")}</div>', unsafe_allow_html=True)

    with tab_chat:
        st.subheader("Interactive Report Inquiry")
        
        # Display chat history in a scrollable area
        chat_placeholder = st.container(height=400)
        with chat_placeholder:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat Input logic
        if query := st.chat_input("Ask a follow-up question..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": query})
            
            # Show user message immediately
            with chat_placeholder:
                with st.chat_message("user"):
                    st.markdown(query)
            
            # Generate AI response
            with chat_placeholder:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        chat_res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are a financial expert. Use the provided context to answer questions accurately."},
                                {"role": "user", "content": f"Context: {st.session_state.full_context[:12000]}\n\nQuestion: {query}"}
                            ]
                        )
                        ans = chat_res.choices[0].message.content
                        st.markdown(ans)
                        st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Important: Rerun to refresh the UI and keep input box active
            st.rerun()

    if os.path.exists(temp_path): os.remove(temp_path)