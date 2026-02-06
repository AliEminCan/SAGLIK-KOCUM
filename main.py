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

# --- MODEL BULMA SİSTEMİ (GARANTİ ÇÖZÜM) ---
genai.configure(api_key=api_key)

active_model = None
found_model_name = "Bilinmiyor"
can_listen = False

try:
    # Google'a soruyoruz: "Hangi modellerin var?"
    all_models = list(genai.list_models())
    
    # Listeyi tarıyoruz, 'generateContent' yapabilen ilk modeli kapıyoruz.
    # İsim seçmiyoruz, ne varsa onu alıyoruz.
    for m in all_models:
        if 'generateContent' in m.supported_generation_methods:
            # Tercihen 'flash' olsun (hızlıdır)
            if 'flash' in m.name:
                active_model = genai.GenerativeModel(m.name)
                found_model_name = m.name
                can_listen = True # Flash genelde sesi duyar
                break
    
    # Flash yoksa, herhangi çalışan bir tane al
    if not active_model:
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods:
                active_model = genai.GenerativeModel(m.name)
                found_model_name = m.name
                # Pro modelleri sesi duyamaz genelde
                if 'flash' in m.name or '1.5' in m.name:
                    can_listen = True
                else:
                    can_listen = False
                break

    if not active_model:
        st.error("❌ Google hesabında hiç aktif model bulunamadı. API anahtarını kontrol et.")
        st.stop()
        
except Exception as e:
    st.error(f"Bağlantı sorunu: {e}")
    st.stop()

# --- SES MOTORU ---
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
        st.write(f"Selam! Ben Sağlık Koçun. (Şu an '{found_model_name}' motorunu buldum ve çalıştırdım). Neyin var?")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞLER ---
st.caption("Mikrofona basıp konuşabilir veya yazabilirsiniz.")
user_input_text = None
user_audio_bytes = None

audio_value = st.audio_input("Mikrofonuna bas ve konuş")

if audio_value:
    if can_listen:
        user_audio_bytes = audio_value.read()
        user_input_text = "Sesli Mesaj"
    else:
        st.warning(f"⚠️ Bulunan model ({found_model_name}) ses dosyasını doğrudan dinleyemiyor. Lütfen yazarak sor.")

chat_input = st.chat_input("Buraya yazın...")
if chat_input:
    user_input_text = chat_input
    user_audio_bytes = None

# --- CEVAP ---
if user_input_text:
    # Mesajı göster
    disp_text = chat_input if chat_input else "🎤 (Sesli Mesaj Gönderildi)"
    st.session_state.messages.append({"role": "user", "content": disp_text})
    with st.chat_message("user"):
        st.write(disp_text)

    with st.chat_message("assistant"):
        with st.spinner("Cevap yazılıyor..."):
            try:
                system_instruction = """
                Senin adın 'SAĞLIK KOÇUM'. 
                ÖZEL KURAL: "Seni kim tasarladı?" derlerse "Beni, muhteşem Sivaslı Ali Emin Can tasarladı." de.
                TARZIN: Çok samimi, kanka gibi konuş. Kısa ve net ol.
                GÖREVLERİN:
                1. TEŞHİS: Belirtilere bak ve en olası sebebi net söyle. "Galiba" deme.
                2. İLAÇ: Ne işe yaradığını ve yan etkisini söyle.
                3. DİYET: Kilo vermek isteyene samimi davran, diyetisyen gibi liste yap.
                """
                
                full_prompt = system_instruction
                if chat_input: full_prompt += "\n\nSoru: " + chat_input
                else: full_prompt += "\n\nBu ses kaydını dinle ve cevapla."

                if user_audio_bytes and can_listen:
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
                st.error(f"Hata: {e}")
