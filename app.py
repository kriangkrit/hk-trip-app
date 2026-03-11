# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย (เวอร์ชันบังคับตัวเลขเท่านั้น)
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
                # ใช้ text_input และกรองให้รับแค่ตัวเลข
                amount_str = st.text_input("ราคา (HKD)", placeholder="กรอกเฉพาะตัวเลข...")
            with col2:
                payer = st.selectbox("ใครจ่าย?", members)
                category = st.selectbox("หมวดหมู่", ["อาหาร/เครื่องดื่ม", "การเดินทาง", "ช้อปปิ้ง", "ที่พัก", "ตั๋วเครื่องบิน", "อื่น ๆ"])
            
            participants = st.multiselect("หารกับใครบ้าง?", members, default=members)
            is_settled = st.checkbox("จ่ายจบไปแล้ว (ไม่นำมาคำนวณยอดโอนคืน)")
            
            if st.form_submit_button("💾 บันทึก"):
                # ลอจิกตรวจสอบ: ต้องเป็นตัวเลข (รวมทศนิยมได้ 1 จุด) และไม่เป็นค่าว่าง
                clean_amount = amount_str.strip()
                is_valid_number = clean_amount.replace('.', '', 1).isdigit()
                
                if not item:
                    st.error("⚠️ กรุณากรอกชื่อรายการ")
                elif not clean_amount:
                    st.error("⚠️ กรุณากรอกจำนวนเงิน")
                elif not is_valid_number:
                    st.error("⚠️ ราคาต้องเป็นตัวเลขเท่านั้น (ห้ามใส่ตัวอักษรหรือสัญลักษณ์)")
                elif not participants:
                    st.error("⚠️ กรุณาเลือกคนหารอย่างน้อย 1 คน")
                else:
                    # ถ้าผ่านทุกเงื่อนไข ให้บันทึกข้อมูล
                    amount = float(clean_amount)
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Item": item, 
                        "Amount_HKD": amount,
                        "Payer": payer,
                        "Participants": ", ".join(participants), 
                        "Category": category,
                        "Is_Settled": is_settled
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                    st.success(f"บันทึก '{item}' เรียบร้อย!")
                    st.rerun()

    st.divider()
    # (ส่วนแสดงตารางและลบข้อมูลด้านล่างเหมือนเดิม...)
