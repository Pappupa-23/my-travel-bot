import streamlit as st
from supabase import create_client, Client
import urllib.parse
import requests

# ---------------- ตั้งค่า LINE Login ----------------
LINE_CLIENT_ID = "2010420584"
LINE_CLIENT_SECRET = "4278d0a8b73b1134bb95b4bbea16a517"
# ลิงก์เว็บ Streamlit ของคุณ (ต้องตรงกับที่ใส่ใน Callback URL เป๊ะๆ และต้องมี / ปิดท้ายถ้าตอนตั้งค่าใส่ไว้)
REDIRECT_URI = "https://my-travel.streamlit.app/"

# ---------------- ระบบ LINE Login ----------------
# เช็คว่าในเซสชันของเว็บมี user_id หรือยัง (ล็อกอินหรือยัง)
if 'user_id' not in st.session_state:
    # --- กรณี 1: เพิ่งกด Allow แล้ว LINE ส่งกลับมาพร้อมรหัส code ใน URL ---
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        
        # นำ code ไปแลกเป็น Access Token
        token_url = "https://api.line.me/oauth2/v2.1/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": LINE_CLIENT_ID,
            "client_secret": LINE_CLIENT_SECRET
        }
        res = requests.post(token_url, headers=headers, data=data)
        
        if res.status_code == 200:
            access_token = res.json().get("access_token")
            # นำ Token ไปดึงโปรไฟล์ User
            profile_url = "https://api.line.me/v2/profile"
            profile_headers = {"Authorization": f"Bearer {access_token}"}
            profile_res = requests.get(profile_url, headers=profile_headers)
            
            if profile_res.status_code == 200:
                profile_data = profile_res.json()
                # 🟢 ล็อกอินสำเร็จ! เก็บ user_id ลงในระบบ
                st.session_state['user_id'] = profile_data['userId']
                st.session_state['display_name'] = profile_data['displayName']
                st.session_state['picture_url'] = profile_data.get('pictureUrl', '')
                
                # ล้าง URL ให้สะอาด แล้วรีเฟรชหน้าเว็บ 1 รอบ
                st.query_params.clear()
                st.rerun()
                
    # --- กรณี 2: เข้าเว็บมาครั้งแรก ยังไม่ล็อกอิน ให้โชว์ปุ่ม ---
    else:
        st.title("กรุณาเข้าสู่ระบบ")
        st.write("โปรดยืนยันตัวตนผ่าน LINE ก่อนนะครับ")
        
        # สร้างลิงก์สำหรับไปหน้า Allow ของ LINE
        auth_url = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={LINE_CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&state=secure_login&scope=profile%20openid"
        
        # 🟢 เปลี่ยนมาใช้คำสั่งนี้แทน มันจะบังคับเปิดหน้าต่าง/แท็บใหม่ให้อัตโนมัติ รอดจาก Iframe แน่นอน
        st.link_button("Login with LINE", url=auth_url, type="primary")
        st.stop() # 🛑 สั่งให้เว็บหยุดทำงานแค่นี้ ไม่ต้องรันโค้ดข้างล่างต่อจนกว่าจะล็อกอิน

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
# แสดงโปรไฟล์คนล็อกอินสวยๆ ที่ Sidebar
st.sidebar.image(st.session_state['picture_url'], width=50)
st.sidebar.write(f"สวัสดีคุณ **{st.session_state['display_name']}**")
st.sidebar.markdown("---")

# ปรับการดึงข้อมูล ให้ดึงเฉพาะที่ added_by ตรงกับ user_id ที่ล็อกอิน
@st.cache_data(ttl=60)
def load_data(user_id):
    response = supabase.table("travel_links").select("*").eq("added_by", user_id).order("created_at", desc=True).execute()
    return response.data

# ดึงข้อมูลมาใช้งาน
data = load_data(st.session_state['user_id'])

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
    
    # --- ส่วนที่ 1: จังหวัด (ใช้ Dropdown เหมือนเดิม เพราะรายชื่อเยอะ พิมพ์ค้นหาได้จะสะดวกกว่า) ---
    default_region = "อื่นๆ"
    for region, provinces in REGIONS_DATA.items():
        if current_prov in provinces:
            default_region = region
            break
            
    if default_region == "อื่นๆ" and current_prov not in REGIONS_DATA["อื่นๆ"]:
        current_prov = "ไม่ระบุ (รอแก้ทีหลัง)"
    
    selected_region = st.selectbox(
        "🗺️ เลือกภูมิภาค", 
        options=list(REGIONS_DATA.keys()), 
        index=list(REGIONS_DATA.keys()).index(default_region)
    )
    
    available_provinces = REGIONS_DATA[selected_region]
    prov_index = available_provinces.index(current_prov) if current_prov in available_provinces else 0
        
    new_province = st.selectbox(
        "📍 เลือกจังหวัด/พื้นที่", 
        options=available_provinces,
        index=prov_index
    )
    
    # --- ส่วนที่ 2: หมวดหมู่ (เปลี่ยนเป็นปุ่มกดแนวนอน จิ้มได้อย่างเดียว พิมพ์ไม่ได้ 100%) ---
    new_category = st.radio(
        "🏷️ หมวดหมู่", 
        options=CATEGORIES_LIST, 
        index=CATEGORIES_LIST.index(current_cat),
        horizontal=True
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
            if st.button("✏️ แก้ไขข้อมูล", key=f"edit_{index}_{item['url']}"):
                edit_dialog(item)
            st.markdown("---")
