import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="HK Trip 2026 🇭🇰", page_icon="🇭🇰", layout="centered")

# --- CSS สำหรับซ่อนปุ่ม + และ - ในช่องตัวเลข ---
st.markdown("""
    <style>
    /* ซ่อนปุ่มบวกและลบใน number input */
    button.step-up {display: none;}
    button.step-down {display: none;}
    div[data-baseweb="input"] > div > div {padding-right: 0;}
    /* ปรับแต่งช่องกรอกให้ดูเหมือน text input ปกติ */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    input[type=number] {
        -moz-appearance: textfield;
    }
    </style>
""", unsafe_allow_stdio=True)

# --- การเชื่อมต่อ Google Sheets ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🇭🇰 Hong Kong Trip 2026")

tab1, tab2, tab3 = st.tabs(["💰 บันทึกค่าใช้จ่าย", "📍 แผนการเดินทาง", "📊 สรุปยอดรวม"])

members = ["KK", "Charlie"]

# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
with tab1:
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
        if 'Is_Settled' not in df.columns:
            df['Is_Settled'] = False
    except:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

    with st.expander("➕ เพิ่มรายการใหม่", expanded=True):
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item = st.text_input("รายการ", placeholder="เช่น ติ่มซำ")
                # กลับมาใช้ number_input แต่ซ่อนปุ่ม +/- ด้วย CSS ด้านบน
                # วิธีนี้จะทำให้บนมือถือเด้งแป้นพิมพ์ตัวเลขเท่านั้น
                amount = st.number_input("ราคา (HKD)", min_value=1, value=None, step=1, placeholder="กรอกตัวเลข...")
            with col2:
                payer = st.selectbox("ใครจ่าย?", members)
                category = st.selectbox("หมวดหมู่", ["อาหาร/เครื่องดื่ม", "การเดินทาง", "ช้อปปิ้ง", "ที่พัก", "ตั๋วเครื่องบิน", "อื่น ๆ"])
            
            participants = st.multiselect("หารกับใครบ้าง?", members, default=members)
            is_settled = st.checkbox("จ่ายจบไปแล้ว (ไม่นำมาคำนวณยอดโอนคืน)")
            
            if st.form_submit_button("💾 บันทึกข้อมูล"):
                if item and amount is not None and participants:
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Item": item, 
                        "Amount_HKD": float(amount),
                        "Payer": payer,
                        "Participants": ", ".join(participants), 
                        "Category": category,
                        "Is_Settled": is_settled
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                    st.success(f"บันทึกเรียบร้อย!")
                    st.rerun()
                else:
                    st.error("⚠️ กรุณากรอก 'รายการ' และ 'ตัวเลขราคา' ให้ถูกต้อง")

    st.divider()
    st.subheader("📝 รายการทั้งหมด")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    
    # ส่วนลบข้อมูล (เหมือนเดิม)
    if not df.empty:
        with st.expander("🗑️ ลบรายการ"):
            list_del = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            sel_del = st.selectbox("เลือกรายการที่จะลบ:", ["-- เลือกรายการ --"] + list_del)
            if sel_del != "-- เลือกรายการ --" and st.button("❌ ยืนยันการลบ"):
                idx = int(sel_del.split(":")[0])
                new_df = df.drop(idx).reset_index(drop=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=new_df)
                st.warning("ลบรายการเรียบร้อยแล้ว")
                st.rerun()

# (ส่วน Tab 2 และ Tab 3 คงเดิมตามเวอร์ชันก่อนหน้า...)
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            with st.expander(f"📅 วันที่ {day}", expanded=True):
                day_items = df_plan[df_plan['Day'] == day]
                for _, row in day_items.iterrows():
                    st.write(f"⏰ **{row['Time']}** : {row['Location']}")
    except: st.info("เตรียมข้อมูลในหน้า Itinerary")

with tab3:
    st.subheader("📊 สรุปยอดค่าใช้จ่าย")
    exch_rate = st.number_input("💵 เรตแลกเงิน (1 HKD = ? THB)", min_value=0.0, value=4.5, step=0.01)
    if not df.empty:
        st.write("### 🍰 สัดส่วนค่าใช้จ่ายทั้งหมด")
        cat_summary = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_summary, values='Amount_HKD', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
        st.write("**💰 รายละเอียดรายหมวดหมู่:**")
        cat_table = cat_summary.copy()
        cat_table['Amount_THB'] = cat_table['Amount_HKD'] * exch_rate
        cat_table.columns = ['หมวดหมู่', 'ยอดรวม (HKD)', 'ยอดรวม (THB)']
        st.table(cat_table.style.format({'ยอดรวม (HKD)': '{:,.2f}', 'ยอดรวม (THB)': '{:,.2f}'}))
        
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE')
        df_for_transfer = df[df['Is_Settled'] == False].copy()
        actual_expense = {m: 0.0 for m in members}
        total_paid = {m: 0.0 for m in members}
        for _, row in df_for_transfer.iterrows():
            total_paid[row['Payer']] += float(row['Amount_HKD'])
            parts = row['Participants'].split(", ")
            share = float(row['Amount_HKD']) / len(parts)
            for p in parts:
                if p in actual_expense: actual_expense[p] += share
        st.divider()
        st.write("### 💰 ยอดที่ต้องโอนคืนกัน (เฉพาะหน้างาน)")
        diff_hkd = total_paid["KK"] - actual_expense["KK"]
        diff_thb = abs(diff_hkd) * exch_rate
        col_res1, col_res2 = st.columns(2)
        with col_res1: st.metric("ยอดโอน (HKD)", f"{abs(diff_hkd):,.2f}")
        with col_res2: st.metric("ยอดโอน (THB)", f"{diff_thb:,.2f}")
        if abs(diff_hkd) < 0.01: st.success("✅ ยอดลงตัวพอดี!")
        elif diff_hkd > 0: st.info(f"🚩 **Charlie** ต้องโอนให้ **KK** 👉 {abs(diff_hkd):,.2f} HKD")
        else: st.info(f"🚩 **KK** ต้องโอนให้ **Charlie** 👉 {abs(diff_hkd):,.2f} HKD")
