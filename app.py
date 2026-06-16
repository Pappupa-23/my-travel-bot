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

# ---------------- ตรวจสอบว่ามีข้อมูลหรือไม่ ----------------
if not data:
    st.info("ยังไม่มีข้อมูลในระบบ ลองส่งลิงก์ TikTok หรือ IG ผ่าน LINE บอทดูสิ!")
else:
    # ---------------- ระบบฟิลเตอร์ (Sidebar) ----------------
    st.sidebar.header("🔍 ค้นหาสถานที่")
    
    # ดึงรายชื่อจังหวัดและหมวดหมู่ทั้งหมดที่มีในฐานข้อมูลมาทำเป็นตัวเลือก
    all_provinces = list(set([item['province'] for item in data if item['province']]))
    all_categories = list(set([item['category'] for item in data if item['category']]))
    
    selected_province = st.sidebar.multiselect("📍 เลือกจังหวัด", all_provinces, default=all_provinces)
    selected_category = st.sidebar.multiselect("🏷️ เลือกหมวดหมู่", all_categories, default=all_categories)
    
    # กรองข้อมูลตามที่ผู้ใช้เลือกใน Sidebar
    filtered_data = [
        item for item in data 
        if item['province'] in selected_province and item['category'] in selected_category
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
            st.markdown("---")