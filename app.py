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

# --- สร้าง Tabs ---
tab1, tab2, tab3 = st.tabs(["💰 บันทึกค่าใช้จ่าย", "📍 แผนการเดินทาง", "📊 สรุปยอดรวม"])

# รายชื่อสมาชิก
members = ["KK", "Charlie"]

# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
with tab1:
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    except:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category"])

    with st.expander("➕ เพิ่มรายการใหม่", expanded=True):
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item = st.text_input("รายการ")
                amount = st.number_input("ราคา (HKD)", min_value=0.0, step=0.1)
            with col2:
                payer = st.selectbox("ใครจ่าย?", members)
                category = st.selectbox("หมวดหมู่", ["อาหาร", "เดินทาง", "ช้อปปิ้ง", "ที่พัก", "ทำบุญ/จิปาถะ", "อื่น ๆ"])
            
            participants = st.multiselect("หารกับใครบ้าง?", members, default=members)
            
            if st.form_submit_button("💾 บันทึก"):
                if item and amount > 0 and participants:
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Item": item, "Amount_HKD": amount, "Payer": payer,
                        "Participants": ", ".join(participants), "Category": category
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                    st.success(f"บันทึก '{item}' เรียบร้อย!")
                    st.rerun()
                else:
                    st.error("กรุณากรอกข้อมูลให้ครบ")

    st.divider()
    st.subheader("📝 รายการทั้งหมด")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    
    if not df.empty:
        with st.expander("🗑️ ลบรายการ"):
            list_del = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            sel_del = st.selectbox("เลือกรายการที่จะลบ", ["-- เลือก --"] + list_del)
            if sel_del != "-- เลือก --" and st.button("❌ ยืนยันลบ"):
                idx = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx).reset_index(drop=True))
                st.rerun()

# ---------------------------------------------------------
# TAB 2: แผนการเดินทาง
# ---------------------------------------------------------
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            with st.expander(f"📅 วันที่ {day}"):
                for _, r in df_plan[df_plan['Day'] == day].iterrows():
                    st.write(f"⏰ **{r['Time']}** : {r['Location']}")
    except: st.info("ไม่มีข้อมูลแผนการเดินทาง")

# ---------------------------------------------------------
# TAB 3: สรุปยอดรวม & รายละเอียดหมวดหมู่
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 สรุปยอดค่าใช้จ่าย")
    
    # ตั้งค่าเรตเงินบาท
    exch_rate = st.number_input("💵 เรตแลกเงิน (1 HKD = ? THB)", min_value=0.0, value=4.5, step=0.01)

    if not df.empty:
        # 1. กราฟหมวดหมู่ค่าใช้จ่าย
        st.write("### 🍰 สัดส่วนค่าใช้จ่ายตามหมวดหมู่")
        cat_summary = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        
        # วาดกราฟ
        fig = px.pie(cat_summary, values='Amount_HKD', names='Category', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        # 2. รายละเอียดใต้กราฟ (ตารางสรุปหมวดหมู่)
        st.write("**รายละเอียดรายหมวดหมู่:**")
        cat_summary_display = cat_summary.copy()
        cat_summary_display['Amount_THB'] = cat_summary_display['Amount_HKD'] * exch_rate
        cat_summary_display.columns = ['หมวดหมู่', 'ยอดรวม (HKD)', 'ยอดรวม (THB)']
        st.table(cat_summary_display.style.format({
            'ยอดรวม (HKD)': '{:,.2f}',
            'ยอดรวม (THB)': '{:,.2f}'
        }))

        # 3. คำนวณ Settlement
        actual_expense = {m: 0.0 for m in members}
        total_paid = {m: 0.0 for m in members}

        for _, row in df.iterrows():
            if row['Payer'] in total_paid:
                total_paid[row['Payer']] += float(row['Amount_HKD'])
            
            parts = row['Participants'].split(", ")
            share = float(row['Amount_HKD']) / len(parts)
            for p in parts:
                if p in actual_expense:
                    actual_expense[p] += share

        # สรุปยอดโอนคืน
        st.divider()
        st.write("### 💰 สรุปยอดโอนคืน")
        
        diff_hkd = total_paid["KK"] - actual_expense["KK"]
        diff_thb = abs(diff_hkd) * exch_rate
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("ยอดโอน (HKD)", f"{abs(diff_hkd):,.2f}")
        with col_res2:
            st.metric("ยอดโอน (THB)", f"{diff_thb:,.2f}")

        if abs(diff_hkd) < 0.01:
            st.success("✅ ยอดลงตัวพอดี ไม่ต้องโอนคืน!")
        elif diff_hkd > 0:
            st.info(f"🚩 **Charlie** ต้องโอนให้ **KK**")
            st.write(f"💸 จำนวน: **{abs(diff_hkd):,.2f} HKD** (ประมาณ **{diff_thb:,.2f} บาท**)")
        else:
            st.info(f"🚩 **KK** ต้องโอนให้ **Charlie**")
            st.write(f"💸 จำนวน: **{abs(diff_hkd):,.2f} HKD** (ประมาณ **{diff_thb:,.2f} บาท**)")
    else:
        st.info("ยังไม่มีข้อมูลค่าใช้จ่าย")
