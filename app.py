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
    
    .stButton>button { 
        border-radius: 12px; border: 1px solid #eee !important; 
        background-color: #ffffff; width: 100%; color: #666;
        font-family: 'Anuphan', sans-serif !important; font-weight: 300 !important;
        text-transform: none !important;
    }

    div.stButton > button:has(div:contains("VIEW VISUAL DIARY")) {
        background-color: #f8f8f8 !important; color: #888 !important;
    }

    div.stButton > button[p-id*="get_dir"] {
        width: auto !important; min-width: 45px !important; padding: 0px 5px !important; 
        min-height: 22px !important; height: 22px !important; font-size: 10px !important; 
        background-color: #f8f8f8 !important; color: #aaa !important;
        border-radius: 6px !important; border: 0.5px solid #eee !important;
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

    st.markdown("<h3 style='text-align: center; font-weight: 300; letter-spacing: 2px;'>ACCESS REQUIRED</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Incorrect password")
    return False

if not check_password():
    st.stop()

# --- Helper Functions ---
def embed_pdf(url):
    try:
        url = url.strip()
        if "drive.google.com" in url:
            if "/d/" in url:
                file_id = url.split("/d/")[1].split("/")[0]
            elif "id=" in url:
                file_id = url.split("id=")[-1].split("&")[0]
            else:
                st.error("❌ Link format incorrect")
                return
            
            embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
            st.markdown(f'''
                <iframe src="{embed_url}" width="100%" height="550px" 
                style="border: none; border-radius: 15px; background: #f9f9f9;">
                </iframe>
            ''', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please use Google Drive link")
    except Exception as e:
        st.error(f"❌ Error: {e}")

@st.dialog("VISUAL DIARY", width="large")
def show_diary(url): st.image(url, use_container_width=True)

# --- Connection ---
# ดึงค่า URL จาก Secrets เพื่อความปลอดภัย (ไม่ให้โชว์ในโค้ด GitHub)
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
                new_row = pd.DataFrame([{
                    "Timestamp": now, "Item": str(item), "Amount_HKD": float(amount), 
                    "Payer": str(payer), "Participants": ", ".join(parts), 
                    "Category": str(cat), "Is_Settled": bool(settled), "Note": str(note)
                }])
                df = df.astype(object)
                df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.toast("Saved! 🥟")
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
                    df = df.astype(object)
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
                    current_settled = str(row['Is_Settled']).upper() == 'TRUE' or row['Is_Settled'] == True
                    u_settled = st.checkbox("Settled", value=current_settled)
                    
                    if st.form_submit_button("UPDATE"):
                        df = df.astype(object)
                        df.at[idx, 'Item'] = str(u_item)
                        df.at[idx, 'Amount_HKD'] = float(u_amt)
                        df.at[idx, 'Payer'] = str(u_payer)
                        df.at[idx, 'Category'] = str(u_cat)
                        df.at[idx, 'Participants'] = ", ".join(u_parts)
                        df.at[idx, 'Note'] = str(u_note)
                        df.at[idx, 'Is_Settled'] = bool(u_settled)
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.success("Updated!")
                        st.rerun()
        st.divider()
        st.dataframe(df.iloc[::-1][['Timestamp', 'Item', 'Amount_HKD', 'Payer']], use_container_width=True, hide_index=True)


# --- TAB 2: PLAN ---
with tab2:
    if st.button("VIEW VISUAL DIARY", use_container_width=True):
        show_diary("https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png")
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            df_plan.columns = [c.strip() for c in df_plan.columns]
            for d in sorted(pd.to_numeric(df_plan['Day']).unique()):
                st.markdown(f"<div class='day-header'>DAY {int(d)}</div>", unsafe_allow_html=True)
                for i, r in df_plan[df_plan['Day'] == d].iterrows():
                    c_txt, c_btn = st.columns([0.82, 0.18])
                    with c_txt:
                        st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
                    with c_btn:
                        if 'Directions_URL' in df_plan.columns and pd.notna(r['Directions_URL']):
                            st.markdown('<div style="margin-top: 18px;"></div>', unsafe_allow_html=True)
                            st.link_button("DIR", r['Directions_URL'], key=f"get_dir_{i}")
                    st.write("")
    except Exception as e: st.info(f"Check Itinerary: {e}")

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
    maps_src = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d118147.68202022026!2d114.1160352!3d22.2922752!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3403f99e4369a19d%3A0x600913959da31416!2sHong%20Kong!5e0!3m2!1sen!2sth!4v1710000000000!5m2!1sen!2sth"
    st.markdown(f'<iframe src="{maps_src}" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
    st.write("")
    st.link_button("OPEN IN GOOGLE MAPS APP", "https://maps.google.com", use_container_width=True)

# --- TAB 5: FILES ---
with tab5:
    st.markdown('<div class="small-header">TRAVEL DOCUMENTS</div>', unsafe_allow_html=True)
    
    # ดึงข้อมูล IDs จาก Secrets
    ids = st.secrets["drive_ids"]

    with st.expander("🏨 SHARED DOCUMENTS", expanded=True):
        if st.checkbox("Hong Kong Personal Travel Plan"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['travel_plan']}/view")
        if st.checkbox("Hotel Confirmation"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['hotel_conf']}/view")
        if st.checkbox("Special Check-in"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['check_in']}/view")

    with st.expander("👤 KK'S DOCUMENTS"):
        if st.checkbox("Disney Park Tickets - KK"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['disney_ticket_kk']}/view")
        if st.checkbox("Disney Premier Access - KK"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['disney_access_kk']}/view")
        if st.checkbox("Meal Voucher 3-in-1 - KK"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['meal_kk']}/view")
        if st.checkbox("Flight Itinerary (DMK-HKG) - KK"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['flight_go_kk']}/view")
        if st.checkbox("Flight Itinerary (HKG-DMK) - KK"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['flight_back_kk']}/view")

    with st.expander("👤 CHARLIE'S DOCUMENTS"):
        if st.checkbox("Disney Park Tickets - TP"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['disney_ticket_ch']}/view")
        if st.checkbox("Disney Premier Access - TP"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['disney_access_ch']}/view")
        if st.checkbox("Meal Voucher 2-in-1 - TP"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['meal_ch']}/view")
        if st.checkbox("Flight Itinerary (DMK-HKG) - TP"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['flight_go_ch']}/view")
        if st.checkbox("Flight Itinerary (HKG-DMK) - TP"):
            embed_pdf(f"https://drive.google.com/file/d/{ids['flight_back_ch']}/view")
