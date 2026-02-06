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

# --- CSS AYARLARI ---
st.markdown("""
<style>
    h1 { color: #2E7D32; text-align: center; }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 5px;
    }
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

# --- MODELİ OTOMATİK BULMA (404 HATASINI BİTİREN KISIM) ---
genai.configure(api_key=api_key)
active_model = None
found_model_name = "Aranıyor..."

try:
    # Google'daki tüm modelleri çek
    all_models = list(genai.list_models())
    
    # Listeden 'generateContent' yapabilen ilk modeli kap
    available_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
    
    if available_models:
        # Varsa Flash'ı tercih et (Hızlıdır)
        selected_model = available_models[0] # Varsayılan olarak ilkini al
        for m in available_models:
            if 'flash' in m.name:
                selected_model = m
                break
        
        active_model = genai.GenerativeModel(selected_model.name)
        found_model_name = selected_model.name
        # Ekrana çalıştığını kanıtlayan yazıyı bas
        st.success(f"✅ BAĞLANTI BAŞARILI! Kullanılan Motor: {found_model_name}")
    else:
        st.error("❌ HATA: Google hesabında hiç aktif model bulunamadı (Liste boş). API Anahtarı hatalı olabilir.")
        st.stop()

except Exception as e:
    st.error(f"❌ BAĞLANTI HATASI: {e}")
    st.stop()

# --- SES MOTORU ---
async def speak_text(text):
    if not text: return None
    try:
        filename = f"cevap_{int(time.time())}.mp3"
