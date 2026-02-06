import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="SAĞLIK KOÇUM",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- BAŞLIK ---
st.markdown("<h1 style='text-align: center; color: #00796B;'>🩺 SAĞLIK KOÇUM</h1>", unsafe_allow_html=True)
st.write("---")

# --- YAN MENÜ ---
with st.sidebar:
    st.success("**Ali Emin Can tarafından yapılmıştır.**")
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen önce sol menüden API anahtarını gir.")
    st.stop()

# --- GEMINI MODELİNİ OTOMATİK BULAN RADAR ---
genai.configure(api_key=api_key)

active_model = None
model_name_log = ""

try:
    # Google'daki tüm modelleri listele
    all_models = list(genai.list_models())
    
    # 1. Öncelik: Gemini 1.5 Flash (En Hızlısı)
    for m in all_models:
        if 'gemini-1.5-flash' in m.name and 'generateContent' in m.supported_generation_methods:
            active_model = genai.GenerativeModel(m.name)
            model_name_log = m.name
            break
    
    # 2. Öncelik: Eğer Flash yoksa Gemini Pro (Eskisi)
    if not active_model:
        for m in all_models:
            if 'gemini-pro' in m.name and 'generateContent' in m.supported_generation_methods:
                active_model = genai.GenerativeModel(m.name)
                model_name_log = m.name
                break
    
    # 3. Öncelik: Hiçbiri yoksa çalışan İLK modeli al
    if not active_model:
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods:
                active_model = genai.GenerativeModel(m.name)
                model_name_log = m.name
                break

    if not active_model:
        st.error("❌ Google API anahtarın doğru ama hiç model bulunamadı. Lütfen anahtarını kontrol et.")
        st.stop()

except Exception as e:
    st.error(f"❌ Bağlantı hatası! Muhtemelen API anahtarı hatalı veya Google servisi meşgul. Hata detayı: {e}")
    st.stop()

# --- SES MOTORU (Nesrin Hanım) ---
async def speak_text(text):
    if not text: return
    try:
        communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
        await communicate.save("cevap.mp3")
    except:
        pass 

# --- ARAYÜZ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.chat_message("assistant"):
        st.write(f"Selam! Ben Sağlık Koçun. (Şu an {model_name_log.split('/')[-1]} motoruyla çalışıyorum). Neyin var, anlat çözelim.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞLER ---
st.caption("Mikrofona bas konuş veya yaz.")
user_input_text = None
user_audio_bytes = None

audio_value = st.audio_input("Mikrofonuna bas ve konuş")

# Ses işleme
if audio_value:
    # Modeli kontrol et, sesi destekliyor mu? (Sadece 'flash' ve '1.5' modelleri sesi destekler)
    if "flash" in model_name_log or "1.5" in model_name_log:
        user_audio_bytes = audio_value.read()
        user_input_text = "Sesli Mesaj"
    else:
        st.warning(f"⚠️ Aktif model ({model_name_log}) sesi doğrudan duyamıyor. Lütfen sorunu yazarak sor.")

chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input_text = chat_input
    user_audio_bytes = None

# --- CEVAP ---
if user_input_text:
    # Kullanıcı mesajını göster
    disp_text = chat_input if chat_input else "🎤 (Sesli Mesaj Gönderildi)"
    st.session_state.messages.append({"role": "user", "content": disp_text})
    with st.chat_message("user"):
        st.write(disp_text)

    with st.chat_message("assistant"):
        with st.spinner("Analiz ediyorum..."):
            try:
                # --- ALİ EMİN CAN PERSONASI ---
                system_instruction = """
                Senin adın 'SAĞLIK KOÇUM'. 
                ÖZEL KURAL: "Seni kim tasarladı?" derlerse GURURLA "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.

                TARZIN:
                1. Çok samimi, içten, kanka gibi konuş. Resmiyet yok.
                2. Kısa ve net ol.

                GÖREVLERİN:
                1. TEŞHİS: "Galiba, olabilir" deme. Belirtilere bak ve en olası sebebi net söyle. (Çok acilse doktora kovla).
                2. İLAÇ: Ne işe yaradığını ve yan etkisini tak tak söyle.
                3. DİYET: Kilo vermek isteyene samimi davran, gaz ver. Diyetisyen gibi profesyonel liste yap.
                """
                
                full_prompt = system_instruction
                if chat_input: full_prompt += "\n\nSoru: " + chat_input
                else: full_prompt += "\n\nBu ses kaydını dinle ve cevapla."

                # Cevabı al
                if user_audio_bytes:
                    response = active_model.generate_content([full_prompt, {"mime_type": "audio/wav", "data": user_audio_bytes}])
                else:
                    response = active_model.generate_content(full_prompt)
                
                ai_response = response.text
                st.write(ai_response)
                
                # Seslendir
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(speak_text(ai_response))
                st.audio("cevap.mp3", autoplay=True)
                
                st.session_state.messages.append({"role": "assistant", "content": ai_response})

            except Exception as e:
                st.error(f"Hata oluştu: {e}")
