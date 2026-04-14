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

    /* --- Login UI Style --- */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 50px 20px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 30px;
        border: 0.5px solid #eee;
        margin-top: 50px;
    }
    .login-title {
        font-size: 28px;
        font-weight: 200 !important;
        letter-spacing: 8px;
        color: #333;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    .login-subtitle {
        font-size: 10px;
        letter-spacing: 4px;
        color: #aaa;
        margin-bottom: 40px;
        text-transform: uppercase;
    }

    div[data-baseweb="input"] {
        background-color: transparent !important;
        border-radius: 0px !important;
        border: none !important;
        border-bottom: 0.5px solid #ddd !important;
    }
    input { text-align: center !important; letter-spacing: 5px !important; color: #555 !important; }

    /* --- General Elements --- */
    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    
    .stButton>button { 
        border-radius: 12px; border: 1px solid #eee !important; 
        background-color: #ffffff; width: 100%; color: #666;
        font-family: 'Anuphan', sans-serif !important; font-weight: 300 !important;
        transition: all 0.4s ease;
    }
    .stButton>button:hover {
        border: 1px solid #ccc !important;
        background-color: #fafafa !important;
        transform: translateY(-1px);
    }

    /* Style พิเศษสำหรับปุ่มใน Tab Files ให้ดูเหมือน List รายการ */
    div.stButton > button[p-id*="doc_btn"] {
        border: none !important;
        border-bottom: 0.5px solid #eee !important;
        border-radius: 0px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding-left: 5px !important;
        color: #555 !important;
        background-color: transparent !important;
        margin-bottom: 2px;
    }

    .small-header { font-size: 16px; font-weight: 400; color: #444; margin-bottom: 15px; letter-spacing: 1px; }
    .day-header { font-size: 16px; font-weight: 400; color: #222; margin: 30px 0 15px 0; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .plan-card { border-left: 1px solid #ddd; padding: 0 0 5px 20px; margin-left: 5px; position: relative; }
    .plan-card::before { content: ''; position: absolute; left: -4px; top: 4px; width: 7px; height: 7px; background-color: #bbb; border-radius: 50%; }
    .time-text { font-size: 11px; color: #aaa; }
    .location-text { font-size: 14px; color: #444; }
    </style>
""", unsafe_allow_html=True)

# --- Login System ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.markdown('<div class="login-container"><div class="login-title">Hong Kong</div><div class="login-subtitle">Journey 2026</div></div>', unsafe_allow_html=True)
        st.text_input("ACCESS CODE", type="password", on_change=password_entered, key="password", label_visibility="collapsed", placeholder="••••")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.markdown("<p style='text-align:center; color:#ff9999; font-size:10px; letter-spacing:2px; margin-top:10px;'>ACCESS DENIED</p>", unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# --- Helper Functions ---
def embed_pdf(url, title="Document"):
    try:
        url = url.strip()
        st.link_button(f"📂 Open {title}", url, use_container_width=True)
        if "drive.google.com" in url:
            if "/d/" in url:
                file_id = url.split("/d/")[1].split("/")[0]
            elif "id=" in url:
                file_id = url.split("id=")[-1].split("&")[0]
            else: return
            embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
            st.markdown(f'<iframe src="{embed_url}" width="100%" height="450px" style="border: none; border-radius: 15px; background: #f9f9f9; margin-top: 10px;"></iframe>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Error: {e}")

@st.dialog("DOCUMENT VIEW", width="large")
def show_doc_dialog(url, title):
    embed_pdf(url, title)

@st.dialog("VISUAL DIARY", width="large")
def show_diary(url): st.image(url, use_container_width=True)

# --- Connection ---
SHEET_URL = st.secrets["gsheets_url"]
conn = st.connection("gsheets", type=GSheetsConnection)
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
except Exception:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])

# --- Main UI ---
st.title("HK TRIP 2026")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY", "🗺️ MAP", "📑 FILES"])

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
                df = pd.concat([df.astype(object), new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.toast("Saved! 🥟")
                st.rerun()

    if not df.empty:
        with st.expander("Edit / Delete"):
            options = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            selected = st.selectbox("Select entry:", options)
            idx = int(selected.split(":")[0])
            row = df.iloc[idx]
            col_e, col_d = st.columns(2)
            with col_d:
                if st.button("DELETE", key=f"del_{idx}", use_container_width=True):
                    df = df.astype(object).drop(idx).reset_index(drop=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()
            with col_e: edit_mode = st.toggle("EDIT", key=f"tog_{idx}")
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
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Payer'], df.at[idx, 'Category'], df.at[idx, 'Participants'], df.at[idx, 'Note'], df.at[idx, 'Is_Settled'] = str(u_item), float(u_amt), str(u_payer), str(u_cat), ", ".join(u_parts), str(u_note), bool(u_settled)
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()
        st.divider()
        st.dataframe(df.iloc[::-1][['Timestamp', 'Item', 'Amount_HKD', 'Payer']], use_container_width=True, hide_index=True)

# --- TAB 2: PLAN ---
with tab2:
    if st.button("VIEW VISUAL DIARY", use_container_width=True): show_diary("https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png")
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            for d in sorted(pd.to_numeric(df_plan['Day']).unique()):
                st.markdown(f"<div class='day-header'>DAY {int(d)}</div>", unsafe_allow_html=True)
                for i, r in df_plan[df_plan['Day'] == d].iterrows():
                    c_txt, c_btn = st.columns([0.82, 0.18])
                    with c_txt: st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
                    with c_btn:
                        if 'Directions_URL' in df_plan.columns and pd.notna(r['Directions_URL']):
                            st.markdown('<div style="margin-top: 18px;"></div>', unsafe_allow_html=True)
                            st.link_button("GET", r['Directions_URL'], key=f"get_dir_{i}")
                    st.write("")
    except Exception: st.info("Check Itinerary Data")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        cat_sum = cat_sum[cat_sum['Amount_HKD'] > 0]
        if not cat_sum.empty:
            fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(
                showlegend=True, 
                margin=dict(t=10, b=10, l=10, r=10), 
                font=dict(family="Anuphan", size=12),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<p style='font-size:10px; font-weight:300; letter-spacing:1.5px; text-align:center; color:#999; text-transform:uppercase;'>Category Breakdown</p>", unsafe_allow_html=True)
            st.table(cat_sum.style.format({'Amount_HKD': '{:,.0f}'}))
            st.divider()

        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
        df['Is_Settled_Bool'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
        
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled_Bool'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip()]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list:
                    if p in bal: bal[p] -= share

        diff = bal["KK"]
        st.markdown(f"""
            <div style="display: flex; justify-content: center; gap: 40px; margin: 20px 0; font-family: 'Anuphan', sans-serif;">
                <div style="text-align: center;">
                    <p style="font-size: 10px; color: #999; letter-spacing: 1px; margin-bottom: 5px; text-transform: uppercase;">Transfer (HKD)</p>
                    <p style="font-size: 18px; font-weight: 300; color: #444; margin: 0;">{abs(diff):,.2f}</p>
                </div>
                <div style="text-align: center;">
                    <p style="font-size: 10px; color: #999; letter-spacing: 1px; margin-bottom: 5px; text-transform: uppercase;">Transfer (THB)</p>
                    <p style="font-size: 18px; font-weight: 300; color: #444; margin: 0;">{abs(diff)*rate:,.0f}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if diff > 0.01: st.info("Charlie → KK")
        elif diff < -0.01: st.info("KK → Charlie")
        else: st.success("Balanced")

        st.markdown("<hr style='border: 0.5px solid #eee; margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:10px; font-weight:300; letter-spacing:1.5px; text-align:center; color:#999; text-transform:uppercase;'>Net Spend Per Person</p>", unsafe_allow_html=True)
        
        usage = {m: 0.0 for m in members}
        user_items = {m: [] for m in members}
        for _, r in df.iterrows():
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip()]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: 
                    if p in usage: 
                        usage[p] += share
                        user_items[p].append(f"{r['Item']} ({share:,.0f})")
        
        usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
        st.table(usage_df.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))
        st.write("") 
        
        kk_list = '<br>'.join([f"• {i}" for i in user_items["KK"]]) if user_items["KK"] else "None"
        ch_list = '<br>'.join([f"• {i}" for i in user_items["Charlie"]]) if user_items["Charlie"] else "None"

        st.markdown(f"""
            <div style="display: flex; justify-content: center; align-items: flex-start; gap: 30px; font-family: 'Anuphan', sans-serif; margin-bottom: 40px;">
                <div style="flex: 0 1 auto; min-width: 130px;">
                    <p style="font-size: 10px; font-weight: 400; color: #aaa; text-align: center; margin-bottom: 12px; letter-spacing: 2px; text-transform: uppercase;">KK's Items</p>
                    <div style="font-size: 11px; color: #777; line-height: 1.8; text-align: center; font-weight: 300;">{kk_list}</div>
                </div>
                <div style="width: 1px; height: 40px; background-color: #eee; align-self: center;"></div>
                <div style="flex: 0 1 auto; min-width: 130px;">
                    <p style="font-size: 10px; font-weight: 400; color: #aaa; text-align: center; margin-bottom: 12px; letter-spacing: 2px; text-transform: uppercase;">Charlie's Items</p>
                    <div style="font-size: 11px; color: #777; line-height: 1.8; text-align: center; font-weight: 300;">{ch_list}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
            
    else: 
        st.info("No data found.")


# --- TAB 4: MAP ---
with tab4:
    st.markdown('<div class="small-header">GOOGLE MAPS</div>', unsafe_allow_html=True)
    st.markdown(f'<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d118147.68202022026!2d114.1160352!3d22.2922752!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3403f99e4369a19d%3A0x600913959da31416!2sHong%20Kong!5e0!3m2!1sen!2sth!4v1710000000000!5m2!1sen!2sth" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
    st.link_button("OPEN IN GOOGLE MAPS APP", "https://maps.google.com", use_container_width=True)

# --- TAB 5: FILES ---
with tab5:
    st.markdown('<div class="small-header">TRAVEL DOCUMENTS</div>', unsafe_allow_html=True)
    ids = st.secrets["drive_ids"]
    
    with st.expander("🏨 SHARED DOCUMENTS", expanded=True):
        if st.button("📄 Hong Kong Personal Travel Plan", key="doc_btn_1", use_container_width=True):
            show_doc_dialog(f"https://drive.google.com/file/d/{ids['travel_plan']}/view", "Travel Plan")
        if st.button("📄 Hotel Confirmation", key="doc_btn_2", use_container_width=True):
            show_doc_dialog(f"https://drive.google.com/file/d/{ids['hotel_conf']}/view", "Hotel Confirmation")
        if st.button("📄 Special Check-in Info", key="doc_btn_3", use_container_width=True):
            show_doc_dialog(f"https://drive.google.com/file/d/{ids['check_in']}/view", "Check-in")

    with st.expander("👤 KK'S DOCUMENTS"):
        docs_kk = [("Disney Park Tickets", ids['disney_ticket_kk']), ("Disney Premier Access", ids['disney_access_kk']), ("Meal Voucher 3-in-1", ids['meal_kk']), ("Flight (DMK-HKG)", ids['flight_go_kk']), ("Flight (HKG-DMK)", ids['flight_back_kk'])]
        for i, (name, d_id) in enumerate(docs_kk):
            if st.button(f"📄 {name}", key=f"doc_btn_kk_{i}", use_container_width=True):
                show_doc_dialog(f"https://drive.google.com/file/d/{d_id}/view", name)

    with st.expander("👤 CHARLIE'S DOCUMENTS"):
        docs_ch = [("Disney Park Tickets", ids['disney_ticket_ch']), ("Disney Premier Access", ids['disney_access_ch']), ("Meal Voucher 2-in-1", ids['meal_ch']), ("Flight (DMK-HKG)", ids['flight_go_ch']), ("Flight (HKG-DMK)", ids['flight_back_ch'])]
        for i, (name, d_id) in enumerate(docs_ch):
            if st.button(f"📄 {name}", key=f"doc_btn_ch_{i}", use_container_width=True):
                show_doc_dialog(f"https://drive.google.com/file/d/{d_id}/view", name)
