import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    /* 1. Import Fonts: Anuphan (Thai No-head) & Montserrat (Eng) */
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, span, div, table, td, th { 
        font-family: 'Anuphan', 'Montserrat', sans-serif !important; 
        font-weight: 300 !important;
        color: #444;
    }

    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-top: -20px; }

    /* 2. FIX: ลบตัวหนังสือ arrow_down / delete ที่ซ้อนทับกัน */
    /* ซ่อน SVG และตัวอักษร Icon ของระบบทั้งหมดในหน้า Expander */
    svg[data-testid="stExpanderIcon"] { display: none !important; }
    span[data-testid="stWidgetLabel"] > div > div > p { font-size: 14px !important; }
    
    /* เจาะจงลบข้อความ icon ที่ชอบหลุดออกมา */
    .st-emotion-cache-p4m0vl, .st-emotion-cache-6q9sum, .data-v-e67c7e { display: none !important; }
    
    /* 3. Buttons Style: มนและบาง */
    .stButton>button {
        border-radius: 12px;
        border: 0.5px solid #eee;
        background-color: #ffffff;
        font-weight: 300 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { border-color: #000; background-color: #fafafa; }

    /* 4. Minimal Inputs: ซ่อนปุ่ม +/- และกรอบบาง */
    button.step-up, button.step-down { display: none !important; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; background-color: transparent !important; }

    /* 5. Metrics & Streamlit UI Cleanup */
    [data-testid="stMetricValue"] { font-weight: 200 !important; font-size: 2.2rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; }
    
    /* ปรับแต่งแถบ Expander ให้ดูเบาบาง */
    div[data-testid="stExpander"] { border: 1px solid #f9f9f9 !important; border-radius: 12px !important; box-shadow: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK TRIP 2026")

tab1, tab2, tab3 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY"])
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

# ---------------------------------------------------------
# TAB 1: EXPENSE
# ---------------------------------------------------------
with tab1:
    # 1. ADD NEW
    with st.expander("➕ ADD NEW", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item", placeholder="e.g. Dim Sum")
            c1, c2 = st.columns(2)
            with c1: 
                amount = st.number_input("Price (HKD)", min_value=1, value=None, step=1, placeholder="0")
            with c2: 
                payer = st.selectbox("Who paid?", members)
            
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            settled = st.checkbox("Settled (Pre-paid)")
            
            if st.form_submit_button("SAVE"):
                if item and amount and parts:
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%y-%m-%d %H:%M"), 
                        "Item": item, "Amount_HKD": float(amount), 
                        "Payer": payer, "Participants": ", ".join(parts), 
                        "Category": cat, "Is_Settled": settled
                    }])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    # 2. EDIT
    if not df.empty:
        with st.expander("✏️ EDIT"):
            list_edit = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            sel_edit = st.selectbox("Select to edit", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Name", value=r['Item'])
                    e_amount = st.number_input("Price", value=float(r['Amount_HKD']), step=1.0)
                    e_payer = st.selectbox("Payer", members, index=members.index(r['Payer']))
                    e_cat = st.selectbox("Category", categories, index=categories.index(r['Category']) if r['Category'] in categories else 0)
                    
                    p_list = str(r['Participants']).split(", ")
                    e_parts = st.multiselect("Split", members, default=[m for m in p_list if m in members])
                    e_settled = st.checkbox("Settled", value=bool(r['Is_Settled']))
                    
                    if st.form_submit_button("UPDATE"):
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Payer'] = e_item, e_amount, e_payer
                        df.at[idx, 'Category'], df.at[idx, 'Participants'], df.at[idx, 'Is_Settled'] = e_cat, ", ".join(e_parts), e_settled
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()

    # 3. DELETE
    if not df.empty:
        with st.expander("🗑️ DELETE"):
            sel_del = st.selectbox("Select to delete", ["-- Select --"] + [f"{i}: {r['Item']}" for i, r in df.iterrows()])
            if sel_del != "-- Select --" and st.button("CONFIRM DELETE"):
                idx = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx).reset_index(drop=True))
                st.rerun()

    st.write("")
    st.dataframe(df.sort_index(ascending=False)[['Item', 'Amount_HKD', 'Payer', 'Category']], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2: PLAN
# ---------------------------------------------------------
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            st.markdown(f"<p style='font-size:18px; font-weight:300; margin-top:15px;'>DAY {day}</p>", unsafe_allow_html=True)
            for _, r in df_plan[df_plan['Day'] == day].iterrows():
                st.markdown(f"<p style='font-size:14px; color:#888; margin-bottom:2px;'>{r['Time']} — {r['Location']}</p>", unsafe_allow_html=True)
    except: st.info("Itinerary data empty.")

# ---------------------------------------------------------
# TAB 3: SUMMARY
# ---------------------------------------------------------
with tab3:
    rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
    
    if not df.empty:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Anuphan", size=14))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<p style='font-weight:300; margin-top:20px;'>BREAKDOWN</p>", unsafe_allow_html=True)
        cat_table = cat_sum.copy()
        cat_table['THB'] = cat_table['Amount_HKD'] * rate
        st.table(cat_table.style.format({'Amount_HKD': '{:,.0f}', 'THB': '{:,.0f}'}))

        # Settlement Calculation
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
        df_unsettled = df[df['Is_Settled'] == False]
        bal = {m: 0.0 for m in members}
        for _, r in df_unsettled.iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = r['Participants'].split(", ")
            for p in p_list: bal[p] -= (float(r['Amount_HKD']) / len(p_list))

        st.divider()
        c1, c2 = st.columns(2)
        diff = bal["KK"] 
        c1.metric("TRANSFER (HKD)", f"{abs(diff):,.2f}")
        c2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
        
        if diff > 0.01: st.info(f"Charlie → KK")
        elif diff < -0.01: st.info(f"KK → Charlie")

        st.write("")
        st.markdown("<p style='font-weight:300;'>NET SPEND PER PERSON</p>", unsafe_allow_html=True)
        usage = {m: 0.0 for m in members}
        for _, r in df.iterrows():
            p_list = r['Participants'].split(", ")
            for p in p_list: usage[p] += (float(r['Amount_HKD']) / len(p_list))
        
        usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
        st.table(usage_df.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))
