import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="HK Trip 2026 🇭🇰", page_icon="🇭🇰", layout="centered")

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
    except:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

    with st.expander("➕ เพิ่มรายการใหม่", expanded=True):
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item = st.text_input("รายการ")
                amount = st.number_input("ราคา (HKD)", min_value=0.0, step=0.1)
            with col2:
                payer = st.selectbox("ใครจ่าย?", members)
                category = st.selectbox("หมวดหมู่", ["ตั๋วเครื่องบิน", "ที่พัก", "อาหาร/เครื่องดื่ม", "การเดินทาง", "ช้อปปิ้ง", "อื่น ๆ"])
            
            participants = st.multiselect("หารกับใครบ้าง?", members, default=members)
            
            # เพิ่มตัวเลือกสำหรับยอดที่เคลียร์กันไปแล้ว
            is_settled = st.checkbox("จ่ายจบไปแล้ว (ไม่นำมาคำนวณยอดโอนคืน)")
            
            if st.form_submit_button("💾 บันทึก"):
                if item and amount > 0 and participants:
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Item": item, "Amount_HKD": amount, "Payer": payer,
                        "Participants": ", ".join(participants), "Category": category,
                        "Is_Settled": is_settled
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                    st.success(f"บันทึกเรียบร้อย!")
                    st.rerun()

    st.divider()
    st.subheader("📝 รายการทั้งหมด")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# ---------------------------------------------------------
# TAB 3: สรุปยอดรวม
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 สรุปยอดค่าใช้จ่าย")
    exch_rate = st.number_input("💵 เรตแลกเงิน (1 HKD = ? THB)", min_value=0.0, value=4.5, step=0.01)

    if not df.empty:
        # 1. กราฟวงกลม (โชว์ทุกอย่าง ทั้งที่จ่ายไปแล้วและยังไม่จ่าย)
        st.write("### 🍰 สัดส่วนค่าใช้จ่ายทั้งหมด")
        cat_summary = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_summary, values='Amount_HKD', names='Category', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        # 2. คำนวณยอดโอน (เฉพาะรายการที่ Is_Settled เป็น False)
        # กรองเอาเฉพาะรายการที่ยังไม่ได้เคลียร์กัน (ยังไม่ Settled)
        df_for_transfer = df[df['Is_Settled'] == False].copy()
        
        actual_expense = {m: 0.0 for m in members}
        total_paid = {m: 0.0 for m in members}

        for _, row in df_for_transfer.iterrows():
            total_paid[row['Payer']] += float(row['Amount_HKD'])
            parts = row['Participants'].split(", ")
            share = float(row['Amount_HKD']) / len(parts)
            for p in parts:
                if p in actual_expense:
                    actual_expense[p] += share

        st.divider()
        st.write("### 💰 ยอดที่ต้องโอนคืนกัน (เฉพาะหน้างาน)")
        
        diff_hkd = total_paid["KK"] - actual_expense["KK"]
        diff_thb = abs(diff_hkd) * exch_rate
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("ยอดโอน (HKD)", f"{abs(diff_hkd):,.2f}")
        with col_res2:
            st.metric("ยอดโอน (THB)", f"{diff_thb:,.2f}")

        if abs(diff_hkd) < 0.01:
            st.success("✅ ยอดหน้างานลงตัวพอดี ไม่ต้องโอนเพิ่ม!")
        elif diff_hkd > 0:
            st.info(f"🚩 **Charlie** ต้องโอนให้ **KK** 👉 **{abs(diff_hkd):,.2f} HKD**")
        else:
            st.info(f"🚩 **KK** ต้องโอนให้ **Charlie** 👉 **{abs(diff_hkd):,.2f} HKD**")

        # 3. สรุปว่าแต่ละคนใช้เงินรวมไปเท่าไหร่ (รวมยอดล่วงหน้าด้วย)
        st.divider()
        st.write("### 👤 สรุปค่าใช้จ่ายต่อคน (รวมทุกอย่าง)")
        
        personal_total = {m: 0.0 for m in members}
        for _, row in df.iterrows():
            parts = row['Participants'].split(", ")
            share = float(row['Amount_HKD']) / len(parts)
            for p in parts:
                if p in personal_total:
                    personal_total[p] += share
        
        for m in members:
            st.write(f"- **{m}** ใช้เงินรวมทั้งทริป: {personal_total[m]:,.2f} HKD (ประมาณ {personal_total[m]*exch_rate:,.2f} บาท)")
            
    else:
        st.info("ยังไม่มีข้อมูล")
