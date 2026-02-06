import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import time

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="SAĞLIK KOÇUM",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS: BALONCUKLAR VE DÜZEN ---
st.markdown("""
<style>
    h1 { color: #2E7D32; text-align: center; }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 5px;
    }
    /* Mikrofonu sabitle */
    .stAudioInput {
        position: fixed;
        bottom: 80px;
        z-index: 99;
        width: 100%;
        background-color: white;
        padding: 5px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    .block-container { padding-bottom: 160px; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown("<h1>🩺 SAĞLIK KOÇUM</h1>", unsafe_allow_html=True)

# --- YAN MENÜ ---
with st.sidebar:
    st.success("**Ali Emin Can tarafından tasarlanmıştır.**")
    st.divider()
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen sol menüden API anahtarını giriniz.")
    st.stop()

# --- MODEL AYARLARI ---
genai.configure(api_key=api_key)
active_model = None

try:
    active_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    active_model = genai.GenerativeModel('gemini-pro')

# --- SES MOTORU ---
async def speak_text(text):
    if not text: return None
    try:
        filename = f"cevap_{int(time.time())}.mp3"
        communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
        await communicate.save(filename)
        return filename
    except:
        return None

# --- HAFIZA VE SAYAÇ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Selam! Ben Sağlık Koçun. Neyin var, anlat bakalım?", "audio": None})

# MİKROFONU SIFIRLAMAK İÇİN SAYAÇ
if "audio_counter" not in st.session_state:
    st.session_state.audio_counter = 0

# --- GEÇMİŞİ GÖSTER ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg and msg["audio"]:
            st.audio(msg["audio"], format='audio/mp3')

# --- GİRİŞ ALANI ---
chat_input = st.chat_input("Buraya yazın...")

# Mikrofon (Sayacı key olarak veriyoruz ki her seferinde sıfırlansın)
audio_value = st.audio_input("🎤 Bas-Konuş", key=f"mic_{st.session_state.audio_counter}")

# Veriyi Yakala
user_input_text = None
user_audio_bytes = None
input_type = None

if chat_input:
    user_input_text = chat_input
    input_type = "text"
elif audio_value:
    user_audio_bytes = audio_value.read()
    if len(user_audio_bytes) > 0:
        user_input_text = "🎤 (Sesli Mesaj)"
        input_type = "audio"

# --- CEVAP MEKANİZMASI ---
if user_input_text:
    # 1. Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": user_input_text})
    with st.chat_message("user"):
        st.write(user_input_text)

    # 2. Asistan Cevabı
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("..."):
            ai_response = ""
            audio_file = None
            
            # --- TRY BLOGU: HATA YAKALAMA BURADA ---
            try:
                system_instruction = """
                Sen 'SAĞLIK KOÇUM'sun. 
                GİZLİ KURAL: "Seni kim tasarladı?" derlerse "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.
                TON: Çok samimi, kanka gibi konuş.
                GÖREVLER:
                1. TEŞHİS: Net konuş. "Galiba" deme.
                2. İLAÇ: Ne işe yarar, yan etkisi ne anlat.
                3. DİYET: Samimi ve profesyonel liste ver.
                """
                
                full_prompt = system_instruction
                if input_type == "text": 
                    full_prompt += f"\n\nSoru: {chat_input}"
                    response = active_model.generate_content(full_prompt)
                else: 
                    full_prompt += "\n\nBu ses kaydını dinle ve samimi cevap ver."
                    response = active_model.generate_content([full_prompt, {"mime_type": "audio/wav", "data": user_audio_bytes}])
                
                ai_response = response.text
                message_placeholder.write(ai_response)
                
                # Sesi oluştur
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_file = loop.run_until_complete(speak_text(ai_response))
                
                if audio_file:
                    st.audio(audio_file, format='audio/mp3', autoplay=True)

                # Hafızaya kaydet
                st.session_state.messages.append({"role": "assistant", "content": ai_response, "audio": audio_file})

            except Exception as e:
                st.error("Bir bağlantı sorunu var, tekrar dener misin?")
            
            # --- RERUN (YENİLEME) GÜVENLİ BÖLGE ---
            # Try-except bittikten sonra burası çalışır. Hata vermez.
            if input_type == "audio":
                time.sleep(1) # Sesin gitmesi için minik bir bekleme
                st.session_state.audio_counter += 1
                st.rerun()
