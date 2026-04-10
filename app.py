import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    html, body, [class*="css"], .stMarkdown { 
        font-family: 'Anuphan', 'Montserrat', sans-serif !important; 
        font-weight: 300 !important;
        color: #444;
    }

    summary > span > div > div { font-size: 0 !important; visibility: hidden !important; }
    summary > span > div > div > p { font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }
    svg[data-testid="stExpanderIcon"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }

    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; width: 100%; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; }

    .small-header {
        font-size: 16px;
        font-weight: 400;
        color: #444; 
        margin: 20px 0 10px 0;
        letter-spacing: 1px;
    }

    /* Table Styling */
    .stDataFrame { border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        for col in ['Item', 'Payer', 'Participants', 'Category', 'Note', 'Timestamp']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None'], '')
    else:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])
except Exception:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])

st.title("HK TRIP 2026")
tab1, tab2, tab3, tab4 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY", "🗺️ MAP"])

# --- TAB 1: EXPENSE ---
with tab1:
    st.markdown('<div class="small-header">ADD ITEM</div>', unsafe_allow_html=True)
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("What did you buy?", placeholder="e.g. Dim Sum")
        c1, c2 = st.columns(2)
        with c1: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0, format="%.0f")
        with c2: payer = st.selectbox("Payer", members)
        c3, c4 = st.columns(2)
        with c3: cat = st.selectbox("Category", categories)
        with c4: parts = st.multiselect("Split", members, default=members)
        note = st.text_input("Note", placeholder="Optional...")
        settled = st.checkbox("Pre-paid (Settled)")
        if st.form_submit_button("SAVE"):
            if item and amount >= 0:
                now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                new_row = pd.DataFrame([{"Timestamp": now, "Item": str(item), "Amount_HKD": float(amount), "Payer": str(payer), "Participants": ", ".join(parts), "Category": str(cat), "Is_Settled": bool(settled), "Note": str(note)}])
                df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.rerun()

    if not df.empty:
        st.write("")
        with st.expander("Edit / Delete"):
            options = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            selected = st.selectbox("Select entry:", options)
            idx = int(selected.split(":")[0])
            row = df.iloc[idx]
            col_e, col_d = st.columns(2)
            with col_d:
                if st.button("DELETE", key=f"del_{idx}", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()
            with col_e:
                edit_mode = st.toggle("EDIT", key=f"tog_{idx}")
            if edit_mode:
                with st.form("edit_form"):
                    u_item = st.text_input("Item", value=str(row['Item']))
                    u_amt = st.number_input("Price", value=float(row['Amount_HKD']))
                    u_payer = st.selectbox("Payer", members, index=members.index(row['Payer']) if row['Payer'] in members else 0)
                    u_cat = st.selectbox("Category", categories, index=categories.index(row['Category']) if row['Category'] in categories else 0)
                    u_parts = st.multiselect("Split with", members, default=[p.strip() for p in str(row['Participants']).split(",") if p.strip() in members])
                    u_note = st.text_input("Note", value=str(row['Note']))
                    u_settled = st.checkbox("Settled", value=bool(row['Is_Settled']))
                    if st.form_submit_button("UPDATE"):
                        df = df.astype(object)
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'] = str(u_item), float(u_amt)
                        df.at[idx, 'Payer'], df.at[idx, 'Category'] = str(u_payer), str(u_cat)
                        df.at[idx, 'Participants'], df.at[idx, 'Note'] = ", ".join(u_parts), str(u_note)
                        df.at[idx, 'Is_Settled'] = bool(u_settled)
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()
        st.divider()
        st.dataframe(df.iloc[::-1][['Timestamp', 'Item', 'Amount_HKD', 'Payer']], use_container_width=True, hide_index=True)

# --- TAB 2: PLAN ---
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            df_plan['Day'] = pd.to_numeric(df_plan['Day'], errors='coerce').fillna(0).astype(int)
            for d in sorted(df_plan['Day'].unique()):
                st.markdown(f"<div class='day-header'>DAY {d}</div>", unsafe_allow_html=True)
                for _, r in df_plan[df_plan['Day'] == d].iterrows():
                    st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except: st.info("Check 'Itinerary' sheet.")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty:
        # 1. กราฟวงกลม
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # 2. การคำนวณเงินโอน (Settlement)
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5)
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: bal[p] -= share

        st.divider()
        c1, c2 = st.columns(2)
        transfer_hkd = abs(bal['KK'])
        c1.metric("TRANSFER (HKD)", f"{transfer_hkd:,.2f}")
        c2.metric("TRANSFER (THB)", f"{transfer_hkd * rate:,.0f}")
        
        if bal['KK'] > 0: st.info("💡 Charlie → KK")
        elif bal['KK'] < 0: st.info("💡 KK → Charlie")
        else: st.success("✅ ทุกคนจ่ายเท่ากันพอดี")

        # 3. สรุปยอดจ่ายจริงของแต่ละคน (Who Paid How Much)
        st.markdown('<div class="small-header">WHO PAID HOW MUCH?</div>', unsafe_allow_html=True)
        
        # คำนวณยอดรวมที่แต่ละคนควักกระเป๋าจ่ายไปจริงๆ (Out-of-Pocket)
        summary_data = []
        for m in members:
            total_paid = df[df['Payer'] == m]['Amount_HKD'].sum()
            summary_data.append({"Member": m, "Total Paid (HKD)": total_paid})
        
        summary_df = pd.DataFrame(summary_data)
        st.table(summary_df.set_index('Member'))

        # 4. ประวัติการจ่ายเงินแยกคน (Detailed History per Payer)
        st.markdown('<div class="small-header">PAYMENT LOG</div>', unsafe_allow_html=True)
        for m in members:
            with st.expander(f"Items paid by {m}"):
                personal_df = df[df['Payer'] == m][['Item', 'Amount_HKD', 'Category', 'Timestamp']]
                if not personal_df.empty:
                    st.dataframe(personal_df.sort_index(ascending=False), use_container_width=True, hide_index=True)
                    st.markdown(f"**Sum:** `{personal_df['Amount_HKD'].sum():,.2f} HKD`")
                else:
                    st.caption("No items found.")
    else:
        st.info("ไม่มีข้อมูลการใช้จ่าย")

# --- TAB 4: MAP ---
with tab4:
    st.markdown('<div class="small-header">GOOGLE MAPS</div>', unsafe_allow_html=True)
    maps_src = "YOUR_GOOGLE_MAPS_EMBED_URL_HERE" # เปลี่ยนเป็น URL ของคุณ
    st.markdown(f'<iframe src="{maps_src}" width="100%" height="500" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
