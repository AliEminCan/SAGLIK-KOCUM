import streamlit as st
import google.generativeai as genai

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="SAĞLIK & SPOR DANIŞMANI",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- TASARIM (SADE VE ŞIK) ---
st.markdown("""
<style>
    /* Ana Başlık */
    h1 { color: #2E7D32; text-align: center; font-family: 'Helvetica', sans-serif; }
    
    /* Sohbet Baloncukları */
    .stChatMessage {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        font-size: 16px;
    }
    
    /* Asistan Mesajı Arka Planı */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #f9f9f9;
        border-left: 5px solid #2E7D32; /* Yeşil şerit */
    }
    
    /* Alt bilgi gizleme */
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown("<h1>🥗 SAĞLIK & SPOR DANIŞMANI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Kişisel Diyet ve Egzersiz Planlayıcınız</p>", unsafe_allow_html=True)

# --- YAN MENÜ ---
with st.sidebar:
    st.info("**Geliştirici:** Sivaslı Ali Emin Can")
    st.divider()
    api_key = st.text_input("Google API Anahtarını Gir:", type="password")

if not api_key:
    st.warning("👉 Lütfen devam etmek için sol menüden API anahtarınızı giriniz.")
    st.stop()

# --- MODEL BAĞLANTISI (OTOMATİK SEÇİM) ---
genai.configure(api_key=api_key)
active_model = None

try:
    # Google'ın elindeki modelleri tara, yazı yazabilen en iyisini seç
    all_models = list(genai.list_models())
    available_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
    
    if available_models:
        # Öncelik Pro modelde (Daha mantıklı ve detaylı yazar)
        selected_model = available_models[0]
        for m in available_models:
            if 'pro' in m.name and 'vision' not in m.name: # Sadece metin odaklı pro modeli tercih et
                selected_model = m
                break
        
        active_model = genai.GenerativeModel(selected_model.name)
        # st.success(f"Bağlantı Kuruldu: {selected_model.name}") # Teknik yazıyı gizledim
    else:
        st.error("Model bulunamadı.")
        st.stop()

except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # İlk karşılama mesajı
    welcome_text = """Merhaba. Ben Sağlık ve Spor Danışmanınızım.
    
Size özel diyet listeleri hazırlayabilir, antrenman programları oluşturabilirim.
Lütfen hedefinizden (kilo alma/verme/kas yapma) bahsedin. Size nasıl yardımcı olabilirim?"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_text})

# --- GEÇMİŞİ GÖSTER ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- GİRİŞ ALANI ---
user_input = st.chat_input("Sorunuzu buraya yazın (Örn: 80 kiloyum, göbek eritmek istiyorum...)")

if user_input:
    # 1. Kullanıcı mesajını ekle ve göster
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 2. Asistan cevabını oluştur
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Program hazırlanıyor, lütfen bekleyin..."):
            try:
                # --- DETAYLI UZMAN MODU ---
                system_instruction = """
                Sen profesyonel bir 'Sağlık ve Spor Danışmanı'sın.
                
                KİMLİK:
                - Yaratıcın: Sivaslı Ali Emin Can. (Sorarlarsa söyle).
                - Ton: Profesyonel, saygılı, açıklayıcı ve yardımsever. "Kanka" gibi konuşma, ama robot gibi soğuk da olma. Güven veren bir uzman dili kullan.

                GÖREVLERİN:
                1. DİYET LİSTESİ: Asla "az ye" diyip geçme. Sabah, Öğle, Akşam ve Ara Öğün şeklinde maddeler halinde DETAYLI liste ver. Besinlerin neden seçildiğini kısaca açıkla (Örn: "Yumurta, tok tutması ve protein için...").
                2. EGZERSİZ: Sadece hareket ismi verme. Set sayısını, tekrar sayısını ve hareketin nereyi çalıştırdığını yaz. (Örn: "3 Set x 12 Tekrar").
                3. DETAY: Kısa cevap verme. Kullanıcıyı bilgilendir, eğit.
                
                ÖNEMLİ UYARI: Her cevabının sonuna veya başına, bunun tıbbi bir reçete olmadığını, ciddi sağlık sorunlarında doktora danışılması gerektiğini nazikçe ekle.
                """
                
                full_prompt = system_instruction + "\n\nKullanıcı Sorusu: " + user_input
                
                response = active_model.generate_content(full_prompt)
                ai_response = response.text
                
                message_placeholder.markdown(ai_response)
                
                # Hafızaya kaydet
                st.session_state.messages.append({"role": "assistant", "content": ai_response})

            except Exception as e:
                st.error("Bir hata oluştu. Lütfen tekrar deneyin.")
