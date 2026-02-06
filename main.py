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

# --- CSS İLE GÖRÜNÜMÜ GÜZELLEŞTİRME ---
st.markdown("""
<style>
    /* Başlık */
    h1 { color: #2E7D32; text-align: center; }
    
    /* Mesaj Baloncukları */
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 5px;
    }
    
    /* Mikrofon Alanı Düzenlemesi */
    .stAudioInput {
        position: fixed;
        bottom: 80px; /* Yazı kutusunun hemen üstü */
        z-index: 99;
        width: 100%;
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0px -2px 10px rgba(0,0,0,0.1);
    }
    
    /* Gereksiz boşlukları sil */
    .block-container { padding-bottom: 150px; }
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
    st.warning("👉 Lütfen sol üstteki menüden anahtarınızı giriniz.")
    st.stop()

# --- MODEL AYARLARI ---
genai.configure(api_key=api_key)
active_model = None

# Modeli sessizce bul
try:
    active_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    active_model = genai.GenerativeModel('gemini-pro')

# --- SES MOTORU ---
async def speak_text(text):
    if not text: return None
    try:
        # Benzersiz dosya ismi (Tarayıcı önbelleği sorunu olmasın diye)
        filename = f"cevap_{int(time.time())}.mp3"
        communicate = edge_tts.Communicate(text, "tr-TR-NesrinNeural")
        await communicate.save(filename)
        return filename
    except:
        return None

# --- SOHBET VE SES HAFIZASI ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Selam! Ben Sağlık Koçun. Neyin var, anlat bakalım?", "audio": None})

# MİKROFONU SIFIRLAMAK İÇİN SAYAÇ (İŞİN SIRRI BURADA)
if "audio_counter" not in st.session_state:
    st.session_state.audio_counter = 0

# --- GEÇMİŞİ GÖSTER ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg and msg["audio"]:
            st.audio(msg["audio"], format='audio/mp3')

# --- GİRİŞ ALANI (SINIRSIZ SES İÇİN ÖZEL KURGU) ---

# 1. Yazı Kutusu (En altta sabit)
chat_input = st.chat_input("Buraya yazın...")

# 2. Mikrofon (Yazının hemen üstünde, her seferinde yenilenen ID ile)
# key=... kısmı sayesinde her mesajdan sonra mikrofon sıfırlanır.
audio_value = st.audio_input("🎤 Bas-Konuş", key=f"mic_{st.session_state.audio_counter}")

# Kullanıcı verisini yakala
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
    # Kullanıcı mesajını ekrana bas
    st.session_state.messages.append({"role": "user", "content": user_input_text})
    with st.chat_message("user"):
        st.write(user_input_text)

    # Asistan cevabı
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("..."):
            try:
                system_instruction = """
                Sen 'SAĞLIK KOÇUM'sun. 
                GİZLİ KURAL: "Seni kim tasarladı?" derlerse GURURLA "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.
                TON: Çok samimi, cana yakın, kanka gibi.
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
                
                # Sesi Hazırla
                audio_file = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                audio_file = loop.run_until_complete(speak_text(ai_response))
                
                if audio_file:
                    st.audio(audio_file, format='audio/mp3', autoplay=True)

                st.session_state.messages.append({"role": "assistant", "content": ai_response, "audio": audio_file})

                # --- KRİTİK NOKTA: MİKROFONU SIFIRLA ---
                # Sayacı artırıyoruz, böylece Stream
