import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import time

# --- SAYFA VE TASARIM AYARLARI ---
st.set_page_config(
    page_title="SAĞLIK KOÇUM",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ÖZEL CSS (PROFESYONEL GÖRÜNÜM İÇİN) ---
st.markdown("""
<style>
    /* Sohbet Baloncukları */
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    /* Kullanıcı Baloncuğu (Sağda, Yeşil) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #DCF8C6;
        border: 1px solid #C3E6CB;
    }
    /* Asistan Baloncuğu (Solda, Beyaz) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
    }
    /* Başlık */
    h1 {
        color: #2E7D32 !important;
        text-align: center;
        font-family: 'Helvetica', sans-serif;
    }
    /* Alt bilgiler ve teknik yazıları gizle */
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown("<h1>🩺 SAĞLIK KOÇUM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Kişisel Dijital Sağlık Asistanınız</p>", unsafe_allow_html=True)

# --- YAN MENÜ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=100) # Temsili ikon
    st.success("**Ali Emin Can tarafından tasarlanmıştır.**")
    st.divider()
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen sol üstteki menüden anahtarınızı giriniz.")
    st.stop()

# --- ARKA PLAN SİSTEMİ (TEKNİK YAZI YOK) ---
genai.configure(api_key=api_key)

# Sessizce modeli buluyoruz, ekrana yazı yazdırmıyoruz.
active_model = None
try:
    # Önce Flash (Ses ve Hız için)
    active_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    # Olmazsa Pro (Yedek)
    active_model = genai.GenerativeModel('gemini-pro')

# --- SES MOTORU (Nesrin Hanım - Dosya Adını Benzersiz Yapıyoruz) ---
async def speak_text(text):
    if not text: return None
    try:
        # Her cevap için benzersiz bir ses dosyası oluşturuyoruz ki tarayıcı eskisiyle karıştırmasın
        filename = f"cevap_{int(time.time())}.mp3"
        communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
        await communicate.save(filename)
        return filename
    except:
        return None

# --- SOHBET HAFIZASI ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # İlk karşılama mesajı
    welcome_msg = "Selam! Ben Sağlık Koçun. Neyin var, nasıl yardımcı olabilirim?"
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg, "audio": None})

# --- GEÇMİŞ MESAJLARI GÖSTER ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # Eğer bu mesajın bir ses kaydı varsa altına oynatıcı koy
        if "audio" in msg and msg["audio"]:
            st.audio(msg["audio"], format='audio/mp3')

# --- GİRİŞ ALANI (PROFESYONEL DÜZEN) ---
st.write("---")
col1, col2 = st.columns([1, 4]) # Mikrofon ve Yazı alanını yan yana veya alt alta düzenle

# Sesli Giriş
audio_value = st.audio_input("🎤 Bas-Konuş")

# Yazılı Giriş
chat_input = st.chat_input("Veya buraya yazın...")

# Kullanıcıdan gelen veriyi işle
user_input_text = None
user_audio_bytes = None
input_type = None

if chat_input:
    user_input_text = chat_input
    input_type = "text"
elif audio_value:
    user_audio_bytes = audio_value.read()
    user_input_text = "🎤 Sesli Mesaj"
    input_type = "audio"

# --- CEVAP MEKANİZMASI ---
if user_input_text:
    # 1. Kullanıcı Mesajını Ekrana Bas
    st.session_state.messages.append({"role": "user", "content": user_input_text})
    with st.chat_message("user"):
        st.write(user_input_text)

    # 2. Asistanın Düşünmesi
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("..."):
            try:
                # Sivaslı Ali Emin Can Kuralları
                system_instruction = """
                Sen 'SAĞLIK KOÇUM'sun. 
                GİZLİ KURAL: "Seni kim tasarladı?" derlerse "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.

                TON: Çok samimi, cana yakın, kanka gibi. Resmiyet yok.
                
                GÖREVLER:
                1. TEŞHİS: Olasılıkları net söyle. "Galiba" deme.
                2. İLAÇ: Ne işe yarar, yan etkisi ne, hemen anlat.
                3. DİYET: Diyetisyen gibi profesyonel ama samimi liste ver.
                """
                
                full_prompt = system_instruction
                if input_type == "text": 
                    full_prompt += f"\n\nSoru: {chat_input}"
                    response = active_model.generate_content(full_prompt)
                else: 
                    full_prompt += "\n\nBu ses kaydını dinle ve samimi bir cevap ver."
                    response = active_model.generate_content([full_prompt, {"mime_type": "audio/wav", "data": user_audio_bytes}])
                
                ai_response = response.text
                
                # Cevabı Yaz
                message_placeholder.write(ai_response)
                
                # Sesi Hazırla (Arka planda)
                audio_file = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                audio_file = loop.run_until_complete(speak_text(ai_response))
                
                # Sesi Çal (Otomatik Oynat)
                if audio_file:
                    st.audio(audio_file, format='audio/mp3', autoplay=True)

                # Hafızaya Kaydet (Hem metni hem sesi)
                st.session_state.messages.append({"role": "assistant", "content": ai_response, "audio": audio_file})

            except Exception as e:
                # Hata olursa teknik detay verme, samimi bir hata mesajı ver
                err_msg = "Şu an küçük bir bağlantı sorunu var kanka, tekrar dener misin?"
                st.error(err_msg)
