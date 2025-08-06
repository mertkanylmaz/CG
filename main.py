import pandas as pd
import streamlit as st
import random
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, firestore
import json
import time

# Firebase ayarları
try:
    # Canvas ortamında __firebase_config değişkeni otomatik olarak sağlanır.
    # Yerel çalıştırmalarda bu değişkenin tanımlı olmaması hataya yol açar.
    if '__firebase_config' in globals():
        firebase_config = json.loads(__firebase_config)
    else:
        # Yerel ortamda çalışıyorsa, yapılandırmayı yerel bir JSON dosyasından oku
        with open('firebase_config.json', 'r') as f:
            file_content = f.read().strip()
            if not file_content:
                st.error("Yerel Firebase yapılandırma dosyası 'firebase_config.json' boş.")
                st.stop()
            firebase_config = json.loads(file_content)

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except FileNotFoundError:
    st.error("Yerel Firebase yapılandırma dosyası 'firebase_config.json' bulunamadı.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"Firebase yapılandırma dosyasında bir hata var. Lütfen formatı kontrol edin: {e}")
    st.stop()
except Exception as e:
    st.error(f"Firebase başlatılırken bir hata oluştu: {e}")
    st.stop()

# Sayfa yapılandırması
st.set_page_config(layout="wide", page_title="Mentor-Öğrenci Sistemi", page_icon="🎓")

# Özel CSS ile daha modern bir tasarım ekleyelim
st.markdown("""
<style>
.stApp {
    background-color: #f0f2f6;
    color: #333;
}
.st-emotion-cache-18ni7ap {
    padding-top: 0rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
.header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(to right, #4a5a70, #2a3a50);
    color: white;
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.header h1 {
    color: white;
    font-size: 2.8em;
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
}
h3 {
    color: #556080;
    border-bottom: 2px solid #556080;
    padding-bottom: 5px;
    margin-top: 30px;
}
.stInfo, .stWarning {
    background-color: #e6f7ff;
    border-left: 5px solid #007bff;
    padding: 10px;
    margin-top: 10px;
    border-radius: 5px;
    color: #004085;
}
.stWarning {
    background-color: #fff3cd;
    border-left-color: #ffc107;
    color: #856404;
}
.stSubheader {
    background-color: #e8ebf0;
    padding: 10px;
    border-radius: 8px;
    font-size: 1.2em;
    font-weight: bold;
}
.mentor-card {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.st-emotion-cache-13k62yr { /* Multiselect and text input container */
    background-color: #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

# İlgi alanları için 20 seçenekli sabit bir liste tanımlayalım
ilgi_secenekleri = [
    "Yazılım Geliştirme", "Veri Bilimi", "Yapısal Mühendislik", "Pazarlama",
    "İnsan Kaynakları", "Proje Yönetimi", "UX/UI Tasarımı", "Grafik Tasarım",
    "Girişimcilik", "Finans", "Makine Öğrenmesi", "Siber Güvenlik",
    "Mobil Uygulama Geliştirme", "Oyun Geliştirme", "E-ticaret",
    "Sosyal Medya Yönetimi", "Yapay Zeka", "Biyoteknoloji", "Robotik",
    "İletişim"
]


# Form gönderme ve session state temizleme için callback fonksiyonu
def submit_form():
    """Form verilerini Firebase'e kaydeder ve form alanlarını temizler."""
    isim = st.session_state.get("isim_input")
    rol = st.session_state.get("rol_input")
    ilgi_alanlari = st.session_state.get("ilgi_alanlari_input")

    if isim and ilgi_alanlari:
        try:
            # Firestore'da belge adını kullanıcı adını temel alarak benzersiz hale getirelim
            doc_ref = db.collection('profiles').document(isim)
            doc_ref.set({
                'isim': isim,
                'rol': rol,
                'ilgi': ilgi_alanlari
            })
            st.success(f"**{isim}** adlı kişinin bilgileri başarıyla kaydedildi!")
            st.session_state.isim_input = ""
            st.session_state.ilgi_alanlari_input = []
        except Exception as e:
            st.error(f"Veri kaydedilirken bir hata oluştu: {e}")
    else:
        st.warning("Lütfen tüm alanları doldurun.")


# Uygulamanın başlığı ve logosu
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Kendi logonuzun URL'sini buraya yapıştırın. Örnek: "https://example.com/logo.png"
    # Eğer logonuz yoksa, yer tutucu görseli kullanmaya devam edebilirsiniz.
    st.image("https://media.licdn.com/dms/image/v2/D4D3DAQHui12ps2UtpQ/image-scale_191_1128/image-scale_191_1128/0/1696624260974/connect_grow_cover?e=1755126000&v=beta&t=RMsXQhZTguL7geeSXTdAOzqoWq1BxfIWyPGaZEZmrQA", use_container_width=True)

st.markdown('<div class="header"><h1>Mentor-Öğrenci Eşleştirme Sistemi</h1></div>', unsafe_allow_html=True)
st.write("Veri eklemek için aşağıdaki formu kullanın.")

with st.form("veri_ekleme_formu"):
    isim = st.text_input("Ad ve Soyad", key="isim_input")
    rol = st.radio("Rolünüz", ("ogrenci", "mezun"), key="rol_input")
    # Kullanıcıdan 5 ilgi alanı seçmesini isteyelim
    ilgi_alanlari = st.multiselect(
        "İlgi Alanları (en fazla 5 tane seçin)",
        ilgi_secenekleri,
        key="ilgi_alanlari_input",
        max_selections=5
    )
    gonder_butonu = st.form_submit_button("Veriyi Gönder", on_click=submit_form)


# Verileri Firebase'den çek
@st.cache_data(ttl=60)  # Verileri 60 saniye önbellekte tut
def get_data_from_firestore():
    docs = db.collection('profiles').stream()
    data = []
    for doc in docs:
        data.append(doc.to_dict())
    return pd.DataFrame(data)


# Verileri çek ve ana işleme başla
df = get_data_from_firestore()

if df.empty:
    st.warning("Veri tabanında kayıtlı hiçbir profil bulunamadı.")
    st.stop()


# İlgi alanlarını string veya list'ten set'e çevirir
def parse_ilgiler(ilgi_data):
    if isinstance(ilgi_data, list):
        return set(i.strip().lower() for i in ilgi_data if i.strip())
    elif isinstance(ilgi_data, str):
        return set(i.strip().lower() for i in ilgi_data.replace(",", ";").split(";") if i.strip())
    else:
        return set()


# Mezunlar ve öğrencileri ayır
mezunlar = df[df["rol"] == "mezun"].copy()
ogrenciler = df[df["rol"] == "ogrenci"].copy()

# Hata ayıklama ve bilgi amaçlı mezun ve öğrenci sayılarını göster
st.info(f"Toplam mezun sayısı: {len(mezunlar)}")
st.info(f"Toplam öğrenci sayısı: {len(ogrenciler)}")

if len(ogrenciler) == 0:
    st.warning("Eşleştirilecek hiç öğrenci bulunamadı.")
    st.stop()

if len(mezunlar) == 0:
    st.warning("Eşleştirme için hiç mezun bulunamadı.")
    st.stop()

# Eşleşme mantığını uygula (Yeni, puanlamalı eşleştirme)
# 1. Mezunların ilgi alanlarını, kontenjanlarını ve eşleşme listesini hazırla
mezun_ilgileri = {row["isim"]: parse_ilgiler(row["ilgi"]) for _, row in mezunlar.iterrows()}
mezun_kontenjan = {isim: [] for isim in mezunlar["isim"]}
mezun_kapasite = {isim: 4 for isim in mezunlar["isim"]}  # Her mezun için max 4 öğrenci

ogrenci_ilgileri = {row["isim"]: parse_ilgiler(row["ilgi"]) for _, row in ogrenciler.iterrows()}
eslesen_ogrenciler = set()

# Tüm olası eşleşmeleri ve puanlarını hesapla
eslesme_adaylari = []
for ogrenci_ismi, o_ilgiler in ogrenci_ilgileri.items():
    for mezun_ismi, m_ilgiler in mezun_ilgileri.items():
        ortak_ilgi_sayisi = len(o_ilgiler.intersection(m_ilgiler))
        if ortak_ilgi_sayisi > 0:
            eslesme_adaylari.append((ortak_ilgi_sayisi, ogrenci_ismi, mezun_ismi))

# Ortak ilgi sayısına göre azalan sırada sırala
eslesme_adaylari.sort(key=lambda x: x[0], reverse=True)

# En yüksek puanlı eşleşmeleri öncelikli olarak atama
for puan, ogrenci, mezun in eslesme_adaylari:
    if ogrenci not in eslesen_ogrenciler and mezun_kapasite[mezun] > 0:
        mezun_kontenjan[mezun].append(ogrenci)
        mezun_kapasite[mezun] -= 1
        eslesen_ogrenciler.add(ogrenci)

# Kalan öğrencileri rastgele, boş kontenjanı olan mezunlara atama
kalan_ogrenciler = [o for o in list(ogrenciler["isim"]) if o not in eslesen_ogrenciler]
random.shuffle(kalan_ogrenciler)

for ogrenci in kalan_ogrenciler:
    bos_kontenjanli_mezunlar = [m for m, kapasite in mezun_kapasite.items() if kapasite > 0]
    if bos_kontenjanli_mezunlar:
        secilen_mezun = random.choice(bos_kontenjanli_mezunlar)
        mezun_kontenjan[secilen_mezun].append(ogrenci)
        mezun_kapasite[secilen_mezun] -= 1
    else:
        st.warning(f"{ogrenci} adlı öğrenci için boş kontenjan kalmadı.")

# Streamlit çıktısı
st.header("Mezunlara Öğrenci Atamaları")
st.info(
    "Aşağıdaki eşleştirmeler, en çok ortak ilgi alanına sahip olanlar öncelikli olmak üzere yapılmıştır. Eşleşme bulunamayan öğrenciler, boş kontenjanı olan mezunlara rastgele atanmıştır.")

for mezun, ogrenci_listesi in mezun_kontenjan.items():
    with st.container():
        st.subheader(f"🎓 {mezun}")
        if not ogrenci_listesi:
            st.write("Eşleşen öğrenci yok.")
            continue

        st.write(f"**Grup Büyüklüğü:** {len(ogrenci_listesi)} öğrenci")

        # Mezunun ilgi alanlarını göster
        mezunun_ilgileri = mezun_ilgileri[mezun]
        st.write(f"**Mezunun İlgi Alanları:** {', '.join(sorted(mezunun_ilgileri)) if mezunun_ilgileri else 'Yok'}")

        st.markdown("---")
        st.markdown("**Öğrenciler:**")

        for ogrenci in ogrenci_listesi:
            # `ogrenci_ilgileri` dictionary'sinden ilgi alanlarını alalım
            ogrenci_ilgileri_set = ogrenci_ilgileri.get(ogrenci, set())

            # Mezunla ortak ilgi alanlarını bulalım
            ortak_ilgiler = mezun_ilgileri.get(mezun, set()).intersection(ogrenci_ilgileri_set)

            # Eşleşme puanını hesaplayalım
            puan = len(ortak_ilgiler)

            # Ortak ilgi alanlarını ve puanı gösterelim
            ilgi_metni = ', '.join(sorted(ogrenci_ilgileri_set)) if ogrenci_ilgileri_set else 'Yok'
            st.write(f"- **{ogrenci}** (İlgi alanları: {ilgi_metni}) - **Ortak İlgi Alanı Puanı:** {puan}")
