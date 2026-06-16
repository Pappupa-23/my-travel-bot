import streamlit as st
from supabase import create_client, Client

# ---------------- ตั้งค่าหน้าเว็บ ----------------
st.set_page_config(page_title="My Travel Collection", page_icon="✈️", layout="wide")
st.title("🗺️ สมุดสะสมที่เที่ยว & ร้านอาหาร")

# ---------------- ตั้งค่า Supabase ----------------
# ใช้ URL ของโปรเจกต์คุณ
SUPABASE_URL = 'https://dfhxqkbiztiajqgcppzi.supabase.co'
# ⚠️ นำ Service Role Key (secret) จากเว็บ Supabase มาวางในเครื่องหมายคำพูดด้านล่างนี้ครับ
SUPABASE_KEY = 'sb_secret_xa81Pdy40ReMVk831uqcPw_SKV5fATl'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- ดึงข้อมูลจากฐานข้อมูล ----------------
# ใช้ st.cache_data เพื่อจำข้อมูลไว้ จะได้ไม่ต้องโหลดใหม่ทุกครั้งที่กดฟิลเตอร์
@st.cache_data(ttl=60) 
def load_data():
    response = supabase.table("travel_links").select("*").execute()
    return response.data

data = load_data()

# ---------------- ข้อมูลหมวดหมู่และภูมิภาค ----------------
REGIONS_DATA = {
    "ภาคกลาง และ กทม.": ["กรุงเทพ", "กรุงเทพมหานคร", "กทม", "bangkok", "bkk", "อยุธยา", "นครปฐม", "นนทบุรี", "ปทุมธานี", "สมุทรปราการ", "สมุทรสาคร", "สมุทรสงคราม", "อัมพวา", "สระบุรี", "ลพบุรี", "สุพรรณบุรี", "นครนายก"],
    "ภาคเหนือ": ["เชียงใหม่", "chiang mai", "เชียงราย", "chiang rai", "แม่ฮ่องสอน", "ปาย", "ลำพูน", "ลำปาง", "แพร่", "น่าน", "nan", "พะเยา", "อุตรดิตถ์", "พิษณุโลก", "สุโขทัย", "เพชรบูรณ์", "เขาค้อ", "ภูทับเบิก", "นครสวรรค์"],
    "ภาคใต้": ["ภูเก็ต", "phuket", "กระบี่", "krabi", "พังงา", "เขาหลัก", "สุราษฎร์ธานี", "สมุย", "พะงัน", "นครศรีธรรมราช", "สิชล", "ตรัง", "พัทลุง", "สงขลา", "หาดใหญ่", "สตูล", "หลีเป๊ะ", "ปัตตานี", "ยะลา", "เบตง", "นราธิวาส", "ชุมพร", "ระนอง"],
    "ภาคตะวันออก": ["ชลบุรี", "พัทยา", "pattaya", "บางแสน", "เกาะล้าน", "ระยอง", "เกาะเสม็ด", "จันทบุรี", "ตราด", "เกาะช้าง", "เกาะกูด", "ฉะเชิงเทรา", "ปราจีนบุรี", "สระแก้ว"],
    "ภาคตะวันตก": ["กาญจนบุรี", "kanchanaburi", "สังขละบุรี", "ราชบุรี", "สวนผึ้ง", "เพชรบุรี", "ชะอำ", "ประจวบคีรีขันธ์", "หัวหิน", "hua hin", "ตาก"],
    "ภาคอีสาน": ["นครราชสีมา", "โคราช", "เขาใหญ่", "khao yai", "ปากช่อง", "ขอนแก่น", "khon kaen", "อุดรธานี", "อุบลราชธานี", "บุรีรัมย์", "สุรินทร์", "ศรีสะเกษ", "ร้อยเอ็ด", "มหาสารคาม", "กาฬสินธุ์", "ชัยภูมิ", "หนองคาย", "หนองบัวลำภู", "เลย", "เชียงคาน", "ภูกระดึง", "สกลนคร", "นครพนม", "มุกดาหาร", "ยโสธร", "อำนาจเจริญ", "บึงกาฬ"],
    "อื่นๆ": ["ไม่ระบุ (รอแก้ทีหลัง)"]
}
CATEGORIES_LIST = ["กิน 🍽️", "พัก 🏨", "เที่ยว 📸", "อื่นๆ 📌"]

# ---------------- ฟังก์ชัน Popup สำหรับแก้ไขข้อมูล ----------------
@st.dialog("📝 แก้ไขรายละเอียดสถานที่")
def edit_dialog(item):
    new_title = st.text_area("ชื่อคลิป / รายละเอียด", value=item['title'])
    
    current_prov = item['province']
    current_cat = item['category'] if item['category'] in CATEGORIES_LIST else "อื่นๆ 📌"
    
    # 🕵️‍♂️ ค้นหาว่าจังหวัดเดิมอยู่ในภาคไหน
    default_region = "อื่นๆ"
    for region, provinces in REGIONS_DATA.items():
        if current_prov in provinces:
            default_region = region
            break
            
    # ถ้าหาไม่เจอจริงๆ ให้ไปตกที่ "อื่นๆ" และกำหนดจังหวัดเป็น "ไม่ระบุ"
    if default_region == "อื่นๆ" and current_prov not in REGIONS_DATA["อื่นๆ"]:
        current_prov = "ไม่ระบุ (รอแก้ทีหลัง)"
    
    # 🔽 กล่องเลือกที่ 1: เลือกภาค (เมื่อเลือกแล้ว จะดึงรายชื่อจังหวัดในภาคนั้นมา)
    selected_region = st.selectbox(
        "🗺️ เลือกภูมิภาค", 
        options=list(REGIONS_DATA.keys()), 
        index=list(REGIONS_DATA.keys()).index(default_region)
    )
    
    # 🔽 กล่องเลือกที่ 2: เลือกจังหวัด (รายการจะเปลี่ยนไปตามภาคที่เลือกด้านบน)
    available_provinces = REGIONS_DATA[selected_region]
    
    # เช็คว่าจังหวัดที่เคยเลือกไว้ ยังอยู่ในภาคที่เพิ่งเปลี่ยนหรือไม่
    prov_index = available_provinces.index(current_prov) if current_prov in available_provinces else 0
        
    new_province = st.selectbox(
        "📍 เลือกจังหวัด/พื้นที่", 
        options=available_provinces,
        index=prov_index
    )
    
    new_category = st.selectbox(
        "🏷️ หมวดหมู่", 
        options=CATEGORIES_LIST, 
        index=CATEGORIES_LIST.index(current_cat)
    )
    
    if st.button("💾 บันทึกการแก้ไข", type="primary"):
        try:
            supabase.table("travel_links").update({
                "title": new_title,
                "province": new_province,
                "category": new_category
            }).eq("url", item['url']).execute()
            
            st.success("บันทึกข้อมูลเรียบร้อย!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# ---------------- ตรวจสอบว่ามีข้อมูลหรือไม่ ----------------
if not data:
    st.info("ยังไม่มีข้อมูลในระบบ ลองส่งลิงก์ TikTok หรือ IG ผ่าน LINE บอทดูสิ!")
else:
    # ---------------- ระบบฟิลเตอร์ (Sidebar) ----------------
    st.sidebar.header("🔍 ค้นหาสถานที่")
    
    all_provinces = list(set([item['province'] for item in data if item['province']]))
    all_categories = list(set([item['category'] for item in data if item['category']]))
    
    # เอา default ออก เพื่อให้กล่องเริ่มต้นแบบโล่งๆ สบายตา
    selected_province = st.sidebar.multiselect("📍 เลือกจังหวัด", all_provinces)
    selected_category = st.sidebar.multiselect("🏷️ เลือกหมวดหมู่", all_categories)
    
    # ปรับลอจิกการกรองใหม่: 
    # ถ้ากล่องว่างเปล่า (not selected_...) ให้ถือว่าผ่านเงื่อนไข (แสดงทั้งหมด)
    filtered_data = [
        item for item in data 
        if (not selected_province or item['province'] in selected_province) and 
           (not selected_category or item['category'] in selected_category)
    ]
    
    st.markdown(f"**พบสถานที่ทั้งหมด {len(filtered_data)} แห่ง**")
    st.markdown("---")

    # ---------------- แสดงผลแบบแกลลอรี (Gallery) ----------------
    # แบ่งหน้าจอเป็น 3 คอลัมน์
    cols = st.columns(3)
    
    for index, item in enumerate(filtered_data):
        # วนลูปเพื่อเอาข้อมูลใส่ลงไปในแต่ละคอลัมน์
        with cols[index % 3]:
            # แสดงรูปหน้าปก (ถ้าไม่มีรูป ให้ใส่รูป Placeholder สีเทาแทน)
            img_url = item['thumbnail'] if item['thumbnail'] else "https://via.placeholder.com/600x400?text=No+Image"
            st.image(img_url, use_container_width=True)
            
            # ตัดชื่อคลิปให้สั้นลงถ้ายาวเกินไป
            display_title = item['title'][:40] + "..." if len(item['title']) > 40 else item['title']
            st.subheader(display_title)
            
            st.write(f"**📍 จังหวัด:** {item['province']}")
            st.write(f"**🏷️ หมวดหมู่:** {item['category']}")
            st.write(f"**👤 โพสต์โดย:** {item['uploader']}")
            
            # ปุ่มกดลิงก์ไปดูคลิป
            st.markdown(f"[▶️ เปิดดูคลิปต้นฉบับ]({item['url']})")
            # ต้องใส่ key ให้ปุ่มด้วย เพื่อไม่ให้ Streamlit สับสนว่าเรากดปุ่มไหน
            if st.button("✏️ แก้ไขข้อมูล", key=f"edit_{item['url']}"):
                edit_dialog(item)
            st.markdown("---")
