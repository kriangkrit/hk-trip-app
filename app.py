import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="HK Trip 2026 🇭🇰", page_icon="🇭🇰", layout="centered")

# --- การเชื่อมต่อ Google Sheets ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🇭🇰 Hong Kong Trip 2026")

# --- สร้าง Tabs ---
tab1, tab2, tab3 = st.tabs(["💰 บันทึกค่าใช้จ่าย", "📍 แผนการเดินทาง", "📊 สรุปยอดรวม"])

# ปรับรายชื่อสมาชิกเป็น 2 คนตามจริง
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
                # เปลี่ยน Dropdown เป็นชื่อ KK และ Charlie
                payer = st.selectbox("ใครจ่าย?", members)
                category = st.selectbox("หมวดหมู่", ["อาหาร", "เดินทาง", "ช้อปปิ้ง", "ที่พัก", "อื่น ๆ"])
            
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
# TAB 3: สรุปยอดรวม (Settlement สำหรับ KK & Charlie)
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 สรุปยอดโอนคืน")
    if not df.empty:
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

        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            st.write("**💰 จ่ายไปจริง**")
            for m in members: st.write(f"{m}: {total_paid[m]:,.2f} HKD")
        with col_sum2:
            st.write("**💸 ยอดที่ต้องหาร**")
            for m in members: st.write(f"{m}: {actual_expense[m]:,.2f} HKD")

        st.divider()
        st.write("### 📢 สรุปการโอนเงิน")
        
        diff = total_paid["KK"] - actual_expense["KK"]
        
        if abs(diff) < 0.01:
            st.success("✅ ยอดลงตัวพอดี ไม่ต้องโอนคืน!")
        elif diff > 0:
            st.info(f"🚩 **Charlie** ต้องโอนให้ **KK** 👉 **{abs(diff):,.2f} HKD**")
        else:
            st.info(f"🚩 **KK** ต้องโอนให้ **Charlie** 👉 **{abs(diff):,.2f} HKD**")
    else:
        st.info("ยังไม่มีข้อมูลค่าใช้จ่าย")
