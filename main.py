import streamlit as st
from openai import OpenAI
import io # Bu yeni kütüphane ses dosyasını tamir edecek

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="SAĞLIK KOÇUM",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ANA BAŞLIK ALANI ---
st.markdown("<h1 style='text-align: center; color: #00796B;'>🩺 SAĞLIK KOÇUM</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #455A64;'>Kişisel Dijital Sağlık Asistanınız</h3>", unsafe_allow_html=True)
st.write("---")

# --- YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    st.write("Bu uygulama, sağlığınızla ilgili sorularınıza yapay zeka destekli yanıtlar verir.")
    st.markdown("**⚠️ Önemli Uyarı:**")
    st.info("Buradaki bilgiler tavsiye niteliğindedir. Kesin tanı ve tedavi için mutlaka doktorunuza başvurun.")
    st.divider()
    api_key = st.text_input("OpenAI API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen başlamak için sol üstteki menüden (>) API anahtarınızı giriniz.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- BOTUN ZEKASI (ALİ EMİN CAN İMZALI) ---
system_prompt = """
Senin adın 'SAĞLIK KOÇUM'. Sen yaşlılar ve sağlık tavsiyesi arayanlar için tasarlanmış, çok bilgili bir asistansın.

KİMLİĞİN VE KONUŞMA TARZIN:
1. Kullanıcıların yaşlı olabileceğini varsayarak; tane tane, basit ve anlaşılır cümleler kur.
2. Sesin bir kadın sesi (Nova) olarak kullanıcıya ulaşacak, nazik ve şefkatli ol.

ÖZEL GİZLİ KURAL (ÇOK ÖNEMLİ):
Eğer kullanıcı sana "Seni kim tasarladı?", "Seni kim yaptı?", "Yaratıcın kim?", "Kimin eserisin?" gibi sorular sorarsa;
Tıbbi kimliğini bir kenara bırak ve gururlu, net bir şekilde sadece şu cevabı ver:
"Beni, muhteşem Sivaslı Ali Emin Can tasarladı."

GÖREVLERİN (DİĞER SORULAR İÇİN):
1. TEŞHİS: Belirtilere göre en yüksek ihtimalli (%99 doğruluk payı ile) durumları sırala ama ASLA kesin teşhis koyma. "Olabilir" de ve doktora yönlendir.
2. İLAÇLAR: Ne işe yaradığını, yan etkilerini ve nasıl kullanıldığını (aç/tok) basitçe anlat.
"""

if "messages" not in st.session_state:
    welcome_msg = "Merhaba! Ben Sağlık Koçunuz. Size nasıl yardımcı olabilirim? Bana şikayetlerinizi anlatabilir veya merak ettiğiniz bir ilacı sorabilirsiniz. Dinliyorum..."
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": welcome_msg}
    ]

# --- SOHBET GEÇMİŞİNİ GÖSTER ---
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

st.write("---")

# --- GİRİŞ ALANI ---
st.subheader("📣 Sorunuzu Sorun")
st.caption("Konuşmanız bitince durdur butonuna basmayı unutmayın.")

# 1. Sesli Giriş
audio_value = st.audio_input("Mikrofonuna bas ve konuş")
prompt = None

if audio_value:
    # --- HATAYI ÖNLEYEN YENİ GÜVENLİK KİLİDİ ---
    # Sesi okuyup ismini zorla 'ses.wav' yapıyoruz ki sistem tanıyamamazlık yapmasın
    audio_bytes = audio_value.read()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "ses.wav" 
    # ------------------------------------------

    with st.spinner("Sesiniz yazıya çevriliyor..."):
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file # Artık düzeltilmiş dosyayı gönderiyoruz
        )
        prompt = transcription.text

# 2. Yazılı Giriş
chat_input = st.chat_input("Veya buraya yazın ve Enter'a basın...")
if chat_input:
    prompt = chat_input

# --- CEVAP VE SESLENDİRME ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Sağlık veritabanı taranıyor..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages
            )
            ai_response = response.choices[0].message.content
            st.markdown(ai_response) 
            
            # Sesi Hazırla
            speech_file_path = "cevap.mp3"
            response_audio = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=ai_response
            )
            response_audio.stream_to_file(speech_file_path)
            
            # Ses oynatıcıyı göster
            st.audio(speech_file_path, autoplay=True)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})
