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
st.markdown("<h3 style='text-align: center; color: #455A64;'>Kişisel Dijital Sağlık Asistanınız</h3>", unsafe_allow_html=True)
st.write("---")

# --- YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    st.success("**Ali Emin Can tarafından yapılmıştır.**")
    st.divider()
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen sol üstteki menüden Google API anahtarınızı giriniz.")
    st.stop()

# --- GEMINI AYARLARI ---
genai.configure(api_key=api_key)

# Sesli görüşme için Flash modelini zorluyoruz (Çünkü sadece o sesi duyabilir)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Google'ın yeni modellerine erişilemiyor. Lütfen API anahtarını kontrol et.")
    st.stop()

# --- SES FONKSİYONU (Nesrin Hanım) ---
async def speak_text(text):
    if not text: return # Boş metin gelirse konuşma
    communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
    await communicate.save("cevap.mp3")

# --- SİSTEM MESAJI ---
system_prompt = """
Senin adın 'SAĞLIK KOÇUM'.
ÖZEL KURAL: "Seni kim tasarladı?" derlerse "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.
GÖREVLERİN:
1. Kısa, net ve anlaşılır cümleler kur samimi ve içtende ol bir arkadaşmış gibi aynı.
2. Tıbbi teşhisleri çok belirleyici ve nokta atışı olsun, "Olabilir,Belki,Galiba" deme Acilse doktora yönlendir.
3. İlaç sorulursa ne işe yaradığını anlat yan etkilerini.
4. Senden kilo vermek isteyenlere çok samimi ve yardımcı ol diyet listesini uzman bir diyetisyen gibi hazırla.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.chat_message("assistant"):
        st.write("Merhaba! Ben Sağlık Koçunuz. Dinliyorum...")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞ ALANI ---
st.caption("Mikrofona basıp konuşabilir veya yazabilirsiniz.")
user_input_text = None
user_audio_bytes = None

# 1. Sesli Giriş
audio_value = st.audio_input("Mikrofonuna bas ve konuş")
if audio_value:
    user_audio_bytes = audio_value.read() # Sesi erkenden oku
    if len(user_audio_bytes) > 0:
        user_input_text = "Sesli Mesaj"
    else:
        st.warning("Ses algılanamadı, lütfen tekrar deneyin.")

# 2. Yazılı Giriş
chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input_text = chat_input
    user_audio_bytes = None # Yazı varsa sesi iptal et

# --- İŞLEM VE CEVAP ---
if user_input_text:
    # Mesajı ekrana bas
    display_text = chat_input if chat_input else "🎤 (Sesli Mesaj Gönderildi)"
    st.session_state.messages.append({"role": "user", "content": display_text})
    with st.chat_message("user"):
        st.write(display_text)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyorum..."):
            try:
                # Sohbeti başlat
                chat = model.start_chat(history=[])
                
                # Soru metni
                prompt_content = system_prompt
                if chat_input:
                     prompt_content += "\n\nSoru: " + chat_input
                else:
                     prompt_content += "\n\nLütfen gönderdiğim ses kaydını dinle ve cevap ver."

                # İsteği Gönder (Sesli veya Yazılı)
                if user_audio_bytes:
                    response = model.generate_content([
                        prompt_content,
                        {"mime_type": "audio/wav", "data": user_audio_bytes}
                    ])
                else:
                    response = model.generate_content(prompt_content)
                
                ai_response = response.text
                st.write(ai_response)
                
                # Sesi Oku
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(speak_text(ai_response))
                st.audio("cevap.mp3", autoplay=True)

                st.session_state.messages.append({"role": "assistant", "content": ai_response})

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
