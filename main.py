import re
import yt_dlp
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from supabase import create_client, Client
import requests 
import uuid

# ตัวแปรจำสถานะการรอรับลิงก์ของแต่ละห้องแชท
listening_chats = {}

app = FastAPI()
# ---------------- หน้าเว็บเปล่าสำหรับให้ UptimeRobot ยิง Ping กระตุก ----------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot is awake!"}

# ---------------- ตั้งค่า LINE API ----------------
LINE_CHANNEL_ACCESS_TOKEN = 'zQ+I9g5CNWhfBujbqB+wVvxdPQ9aMBl4QVxuPPfKSnjQwIvH/Ddliuv0lHnbYf8+OsvxJ/MBObmYoE87PglYbRNUGOqwW673G/zBMXMEKBlZrm2zjSakUiY0gLnYJ0LpUuaQGhJzSPY4j7c8bbHB2QdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '61041fb21f74a2bc4e16c6bc4cfbec1f'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ---------------- ตั้งค่า Supabase ----------------
# ใช้ Project ID ของคุณสร้าง URL ได้เลย
SUPABASE_URL = 'https://dfhxqkbiztiajqgcppzi.supabase.co'
# ⚠️ นำ Service Role Key (secret) ที่ก็อปมา วางในเครื่องหมายคำพูดด้านล่างนี้ครับ
SUPABASE_KEY = 'sb_secret_xa81Pdy40ReMVk831uqcPw_SKV5fATl' 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# ฐานข้อมูลคำค้นหา
# ==========================================
PROVINCES = {
    # ภาคกลาง และ กทม.
    "กรุงเทพ", "กรุงเทพมหานคร", "กทม", "bangkok", "bkk", "อยุธยา", "นครปฐม", "นนทบุรี", 
    "ปทุมธานี", "สมุทรปราการ", "สมุทรสาคร", "สมุทรสงคราม", "อัมพวา", "สระบุรี", "ลพบุรี", 
    "สุพรรณบุรี", "นครนายก",
    
    # ภาคเหนือ
    "เชียงใหม่", "chiang mai", "เชียงราย", "chiang rai", "แม่ฮ่องสอน", "ปาย", "ลำพูน", 
    "ลำปาง", "แพร่", "น่าน", "nan", "พะเยา", "อุตรดิตถ์", "พิษณุโลก", "สุโขทัย", "เพชรบูรณ์", 
    "เขาค้อ", "ภูทับเบิก", "นครสวรรค์",
    
    # ภาคใต้
    "ภูเก็ต", "phuket", "กระบี่", "krabi", "พังงา", "เขาหลัก", "สุราษฎร์ธานี", "สมุย", 
    "พะงัน", "นครศรีธรรมราช", "สิชล", "ตรัง", "พัทลุง", "สงขลา", "หาดใหญ่", "สตูล", 
    "หลีเป๊ะ", "ปัตตานี", "ยะลา", "เบตง", "นราธิวาส", "ชุมพร", "ระนอง",
    
    # ภาคตะวันออก
    "ชลบุรี", "พัทยา", "pattaya", "บางแสน", "เกาะล้าน", "ระยอง", "เกาะเสม็ด", "จันทบุรี", 
    "ตราด", "เกาะช้าง", "เกาะกูด", "ฉะเชิงเทรา", "ปราจีนบุรี", "สระแก้ว",
    
    # ภาคตะวันตก
    "กาญจนบุรี", "kanchanaburi", "สังขละบุรี", "ราชบุรี", "สวนผึ้ง", "เพชรบุรี", "ชะอำ", 
    "ประจวบคีรีขันธ์", "หัวหิน", "hua hin", "ตาก",
    
    # ภาคอีสาน
    "นครราชสีมา", "โคราช", "เขาใหญ่", "khao yai", "ปากช่อง", "ขอนแก่น", "khon kaen", 
    "อุดรธานี", "อุบลราชธานี", "บุรีรัมย์", "สุรินทร์", "ศรีสะเกษ", "ร้อยเอ็ด", "มหาสารคาม", 
    "กาฬสินธุ์", "ชัยภูมิ", "หนองคาย", "หนองบัวลำภู", "เลย", "เชียงคาน", "ภูกระดึง", 
    "สกลนคร", "นครพนม", "มุกดาหาร", "ยโสธร", "อำนาจเจริญ", "บึงกาฬ"
}

CATEGORIES = {
    "กิน 🍽️": [
        "ชิม", "คาเฟ่", "ร้านอาหาร", "ของกิน", "อร่อย", "หิว", "กาแฟ", "ขนม", "ของหวาน",
        "ชาบู", "หมูกระทะ", "บุฟเฟ่ต์", "บาร์", "เหล้า", "เบียร์", "สตรีทฟู้ด", "มิชลิน", 
        "cafe", "restaurant", "food", "coffee", "bar", "buffet", "eat", "drink"
    ],
    "พัก 🏨": [
        "ที่พัก", "โรงแรม", "รีสอร์ท", "โฮมสเตย์", "กางเต็นท์", "เต็นท์", "แคมป์ปิ้ง", 
        "พูลวิลล่า", "โฮสเทล", "ห้องพัก", "นอนไหน", "ที่นอน",
        "hotel", "resort", "hostel", "villa", "homestay", "camp", "accommodation", "stay"
    ],
    "เที่ยว 🏞️": [
        "ที่เที่ยว", "เที่ยว", "จุดชมวิว", "ทะเล", "ภูเขา", "น้ำตก", "วัด", "มิวเซียม", 
        "พิพิธภัณฑ์", "สวนสัตว์", "ถ่ายรูป", "มุมถ่ายรูป", "แลนด์มาร์ค", "อุทยาน", "ธรรมชาติ",
        "น้ำขึ้น", "พระอาทิตย์ตก", "สวยมาก", "วิว", "บรรยากาศดี", 
        "attraction", "travel", "viewpoint", "beach", "mountain", "waterfall", "temple", "museum", "sunset", "view"
    ],
    "เดินทาง 🚗": [
        "การเดินทาง", "รถไฟ", "รถบัส", "รถทัวร์", "เครื่องบิน", "ตั๋วเครื่องบิน", "สนามบิน", 
        "เช่ารถ", "รถเช่า", "รถตู้", "บีทีเอส", "bts", "mrt", "เรือ", 
        "transport", "flight", "train", "bus", "car rental", "airport", "ticket"
    ],
    "ช้อปปิ้ง 🛍️": [
        "ตลาด", "ห้าง", "ช้อปปิ้ง", "ซื้อของ", "ของฝาก", "ถนนคนเดิน", "ตลาดนัด", "ตลาดกลางคืน",
        "market", "shopping", "mall", "souvenir", "walking street", "night market"
    ]
}

# ---------------- ฟังก์ชันช่วยเหลือ ----------------
def analyze_text(text):
    text = text.lower()
    found_province = "ไม่ระบุ (รอแก้ทีหลัง)"
    found_category = "อื่นๆ 📌"

    for p in PROVINCES:
        if p in text:
            if p in ["bangkok"]: found_province = "กรุงเทพ"
            elif p in ["พัทยา"]: found_province = "ชลบุรี"
            elif p in ["เขาใหญ่"]: found_province = "นครราชสีมา"
            elif p in ["หัวหิน"]: found_province = "ประจวบคีรีขันธ์"
            else: found_province = p
            break
            
    for cat, keywords in CATEGORIES.items():
        if any(kw in text for kw in keywords):
            found_category = cat
            break
            
    return found_province, found_category

def extract_url(text):
    url_pattern = re.compile(r'https?://\S+')
    match = url_pattern.search(text)
    return match.group(0) if match else None

def fetch_video_data(url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
            raw_title = info.get('title') or ""
            raw_desc = info.get('description') or ""
            
            # 🟢 ฟังก์ชันผ่าตัดล้างขยะ (ปรับให้จับเฉพาะ views, reactions, shares)
            def clean_garbage_text(text):
                if not text: 
                    return ""
                text = str(text).strip()
                
                # สเต็ปที่ 1: ถ้าเจอ | ให้เช็คว่าฝั่งซ้ายมีคำที่ระบุไหม ถ้ามี ให้เอาเฉพาะฝั่งขวา
                if "|" in text:
                    parts = text.split("|", 1)
                    left_side = parts[0].lower()
                    if any(w in left_side for w in ["views", "reactions", "shares"]):
                        text = parts[1].strip()
                
                # สเต็ปที่ 2: เผื่อกรณีที่ TikTok ไม่ส่ง | มาให้ แต่ขึ้นต้นด้วยยอดวิวตรงๆ
                text = re.sub(r'^\s*\d+(\.\d+)?[KMkm]?\s*(views|reactions|shares)\s*·?\s*', '', text, flags=re.IGNORECASE)
                
                # สเต็ปที่ 3: ล้างเครื่องหมายคำพูดขยะที่ติดมาข้างหน้า
                text = text.lstrip('”"\'‘“ ')
                
                return text.strip()

            # นำข้อความมาผ่านกระบวนการทำความสะอาด
            cleaned_title = clean_garbage_text(raw_title)
            cleaned_desc = clean_garbage_text(raw_desc)
            
            # เลือกว่าจะใช้ Title หรือ Description
            if cleaned_title and len(cleaned_title) > 2:
                final_title = cleaned_title
            elif cleaned_desc and len(cleaned_desc) > 2:
                final_title = cleaned_desc
            else:
                final_title = "คลิปน่าสนใจ (ไม่มีแคปชั่น)"

            text_to_analyze = f"{cleaned_title} {cleaned_desc}".strip()

            return {
                "title": final_title,
                "uploader": info.get('uploader') or info.get('creator') or "ไม่ทราบชื่อผู้โพสต์",
                "thumbnail": info.get('thumbnail') or "",
                "description": text_to_analyze 
            }
            
        except Exception as e:
            print(f"[Error] fetch_video_data: {e}")
            return None

# ---------------- Webhook Route ----------------
@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    body_str = body.decode('utf-8')

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

# ---------------- ฟังก์ชันอัปโหลดรูป ----------------
def upload_image_to_supabase(image_url):
    try:
        # ดาวน์โหลดรูปจาก IG/TikTok
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            file_name = f"{uuid.uuid4()}.jpg"
            # อัปโหลดเข้า Storage Bucket ชื่อ 'images'
            supabase.storage.from_("images").upload(
                file=response.content,
                path=file_name,
                file_options={"content-type": "image/jpeg"}
            )
            # ดึง URL ของรูปที่อัปโหลดสำเร็จ
            return supabase.storage.from_("images").get_public_url(file_name)
    except Exception as e:
        print(f"[Storage Error] {e}")
    return image_url # ถ้าอัปโหลดไม่ผ่าน ให้ใช้ลิงก์เดิมไปก่อน

# ---------------- จัดการข้อความที่รับเข้ามา ----------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text_received = event.message.text
    source_type = event.source.type
    user_id = event.source.user_id # เก็บรหัสคนพิมพ์ไว้ทำ Log
    
    # ---------------- 🟢 2. แยกแยะ ID ของห้องแชท ----------------
    if source_type == 'group':
        chat_id = event.source.group_id
    elif source_type == 'room':
        chat_id = event.source.room_id
    else:
        chat_id = event.source.user_id
        
    print(f"[Log] Source: {source_type} ({chat_id}) | User: {user_id} ส่งข้อความ: {text_received}")
    
    url = extract_url(text_received)
    has_link = bool(url)

    # ---------------- 🟢 3. บริหารจัดการโหมดการทำงาน ----------------
    
    # กรณีที่ 1: คุยส่วนตัวกับบอทแบบ 1-on-1 (ไม่ต้องใช้คีย์เวิร์ด)
    if source_type == 'user':
        if not url:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ส่งมาแค่ลิงก์ TikTok หรือ IG ได้เลยนะครับ 📌")
            )
            return
        # ถ้ามี URL ระบบจะไหลลงไปทำงานส่วนดึงข้อมูลด้านล่างต่อทันที
        
    # กรณีที่ 2: อยู่ในกลุ่ม (Group) หรือ แชทหลายคน (Room)
    else:
        # เช็คคำสั่ง "ปลุกบอท"
        trigger_keywords = ["ไปเที่ยวกัน", "เซฟที่นี่", "เรียกบอท"]
        if any(keyword in text_received for keyword in trigger_keywords):
            listening_chats[chat_id] = True # เปิดโหมดรอฟังให้ห้องนี้
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="🎒 พร้อมจดแล้ว! ส่งลิงก์สถานที่มาได้เลยครับ (หรือพิมพ์ 'ยกเลิก' เพื่อปิดการจด)")
            )
            return
            
        # เช็คสถานะว่าห้องนี้กำลังอยู่ในโหมด "รอฟังลิงก์" อยู่หรือไม่?
        if listening_chats.get(chat_id) == True:
            if text_received == "ยกเลิก":
                listening_chats[chat_id] = False # ปิดโหมดแมนนวล
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="โอเคครับ พับสมุดเก็บเรียบร้อย 😅")
                )
                return
            elif has_link:
                # ได้ลิงก์สมใจแล้ว! สั่งปิดโหมดรอฟังทันที แล้วไหลลงไปทำงานด้านล่าง
                listening_chats[chat_id] = False
            else:
                # ถ้ากำลังรอลิงก์อยู่ แต่คนในกลุ่มพิมพ์คุยเรื่องอื่น ให้บอทอยู่เงียบๆ ไม่ตอบโต้
                return
        else:
            # ถ้าไม่ได้ปลุกบอท และบอทก็ไม่ได้รอฟังอยู่ ให้เงียบสนิท 100% ไม่กวนแชทกลุ่ม
            return

    # ---------------- 🟢 4. ส่วนวิเคราะห์ บันทึกข้อมูล และส่ง Flex Message ----------------
    # (ใช้ลอจิกเดิมของคุณ แต่เปลี่ยนปลายทางเป็น chat_id)
    
    # ตอบกลับก่อนว่ากำลังทำงาน
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="กำลังวิเคราะห์และบันทึกข้อมูล... รอแป๊บนึงนะครับ ⏳")
    )
        
    video_data = fetch_video_data(url)
        
    if video_data:
        text_to_analyze = f"{video_data['uploader']} {video_data['description']}"
        province, category = analyze_text(text_to_analyze)
        
        try:
            permanent_thumbnail = upload_image_to_supabase(video_data['thumbnail'])
            
            db_data = {
                "url": url,
                "title": video_data['title'][:100],
                "province": province,
                "category": category,
                "uploader": video_data['uploader'],
                "thumbnail": permanent_thumbnail, 
                "added_by": chat_id # 🟢 เปลี่ยนจาก user_id เป็น chat_id เพื่อระบุว่าเป็นของกลุ่ม/ห้องนี้
            }
            supabase.table("travel_links").insert(db_data).execute()
            
            # สร้าง Flex Message JSON (ใช้โค้ดโครงสร้างสวยงามตัวเดิมของคุณ)
            flex_json = {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": video_data['thumbnail'] if video_data['thumbnail'] else "https://via.placeholder.com/600x400?text=No+Image",
                    "size": "full",
                    "aspectRatio": "16:9",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": video_data['title'][:40] + "..." if len(video_data['title']) > 40 else video_data['title'],
                            "weight": "bold",
                            "size": "md",
                            "wrap": True
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {"type": "text", "text": "📍 จังหวัด", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                        {"type": "text", "text": province, "wrap": True, "color": "#666666", "size": "sm", "flex": 5}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {"type": "text", "text": "🏷️ หมวด", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                        {"type": "text", "text": category, "wrap": True, "color": "#666666", "size": "sm", "flex": 5}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {"type": "text", "text": "👤 โพสต์โดย", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                        {"type": "text", "text": video_data['uploader'], "wrap": True, "color": "#666666", "size": "sm", "flex": 5}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "height": "sm",
                            "color": "#06C755", 
                            "action": {
                                        "type": "uri",
                                        "label": "เปิดดูคลิปต้นฉบับ",
                                        "uri": url
                                    }
                        }
                    ],
                    "flex": 0
                }
            }
            
            msg_to_send = FlexSendMessage(alt_text="บันทึกสถานที่สำเร็จ!", contents=flex_json)
            
        except Exception as db_err:
            print(f"[Database Error] บันทึกไม่สำเร็จ: {db_err}")
            msg_to_send = TextSendMessage(text="❌ ดึงข้อมูลได้ แต่บันทึกลงฐานข้อมูลไม่สำเร็จครับ")
    else:
        msg_to_send = TextSendMessage(text="❌ ดึงข้อมูลไม่สำเร็จครับ อาจจะเป็นลิงก์ส่วนตัว หรือระบบขัดข้อง")

    # 🟢 เปลี่ยนจาก user_id เป็น chat_id เพื่อให้บอทพ่นการ์ด Flex กลับมาในกลุ่ม ไม่ใช่กระซิบส่วนตัวไปหาคนส่ง
    line_bot_api.push_message(chat_id, msg_to_send)

