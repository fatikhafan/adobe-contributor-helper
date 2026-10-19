import io
import os
import ftplib
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from google import genai
from streamlit_image_comparison import image_comparison

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Adobe Stock Contributor Helper",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ Adobe Contributor Helper")
st.caption("AI Title & Keywords | Smart AI Sharp Upscale | Direct FTP Upload")

# --- SIDEBAR KONFIGURASI ---
st.sidebar.header("⚙️ Pengaturan")
gemini_api_key = st.sidebar.text_input("Gemini AI API Key", type="password", help="API Key gratis dari Google AI Studio")

# Pilihan Mode Upload
upload_mode = st.sidebar.radio(
    "Pilih Mode Upload:",
    ["Manual Upload (Download File)", "Auto Upload (FTP Adobe Stock)"]
)

ftp_host = "ftp.stock.adobe.com"
ftp_user = ""
ftp_pass = ""

if upload_mode == "Auto Upload (FTP Adobe Stock)":
    st.sidebar.subheader("🔑 Kredensial FTP")
    ftp_user = st.sidebar.text_input("FTP Username", value=st.session_state.get('ftp_user', ''))
    ftp_pass = st.sidebar.text_input("FTP Password", type="password", value=st.session_state.get('ftp_pass', ''))
    if st.sidebar.button("Simpan FTP"):
        st.session_state['ftp_user'] = ftp_user
        st.session_state['ftp_pass'] = ftp_pass
        st.sidebar.success("Kredensial FTP Disimpan!")

st.markdown("---")

# --- FORM UTAMA ---
col_lang, col_scale = st.columns(2)

with col_lang:
    selected_language = st.selectbox(
        "🌐 Bahasa Metadata (Title & Keywords):",
        [
            "English", 
            "Français", 
            "Deutsch", 
            "Español", 
            "Italiano", 
            "Português", 
            "日本語", 
            "Polski", 
            "한국어",
            "Indonesian"
        ],
        index=0
    )

with col_scale:
    scale_factor = st.selectbox("🔍 Skala Upscale (Resolusi):", [2, 4, 8], index=1, help="Pilih 4x atau 8x jika foto asli berukuran kecil")

uploaded_file = st.file_uploader("📸 Upload Foto / Gambar di Sini", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    if original_image.mode in ("RGBA", "P"):
        original_image = original_image.convert("RGB")

    width, height = original_image.size
    st.info(f"📐 Resolusi Asli: {width} x {height} piksel")

    if st.button("🚀 Proses Gambar Sekarang", type="primary"):
        if not gemini_api_key:
            st.error("⚠️ Harap masukkan Gemini AI API Key di menu Pengaturan sebelah kiri!")
        else:
            processed_image = original_image.copy()

            # 1. AI METADATA GENERATION DENGAN AUTO FALLBACK
            with st.spinner("1️⃣ Menganalisis gambar & membuat metadata..."):
                client = genai.Client(api_key=gemini_api_key)
                prompt = f"""
                Analyze this image for Adobe Stock Contributor submission.
                Generate metadata strictly in language: {selected_language}.
                Output format MUST be EXACTLY as follows:
                Title: <Descriptive title max 15 words in {selected_language}>
                Keywords: <30-40 relevant keywords separated by commas in {selected_language}>
                """

                models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro']
                ai_success = False

                for model_name in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[original_image, prompt]
                        )
                        ai_text = response.text
                        st.success(f"✓ AI Berhasil Generate Title & Keywords (Model: {model_name})!")
                        st.text_area("📋 Hasil AI Metadata (Silakan Copy-Paste):", value=ai_text, height=140)
                        ai_success = True
                        break
                    except Exception as err:
                        continue

                if not ai_success:
                    st.error("⚠️ Server Gemini AI sedang padat. Silakan klik tombol 'Proses Gambar Sekarang' sekali lagi.")

            # 2. PROSES UPSCALE & SHARPNESS ENHANCEMENT
            with st.spinner(f"2️⃣ Memperbesar resolusi gambar ({scale_factor}x) & Mempertajam detail..."):
                new_width, new_height = width * scale_factor, height * scale_factor
                
                # Resizing dengan algoritma Lanczos
                processed_image = original_image.resize((new_width, new_height), Image.LANCZOS)
                
                # Penajaman Detail (Sharpening & Contrast)
                enhancer_sharp = ImageEnhance.Sharpness(processed_image)
                processed_image = enhancer_sharp.enhance(2.0)
                
                enhancer_contrast = ImageEnhance.Contrast(processed_image)
                processed_image = enhancer_contrast.enhance(1.1)

                st.success(f"✓ Resolusi berhasil dinaikkan dari {width}x{height} menjadi {new_width} x {new_height} piksel!")

                st.subheader("🔍 Perbandingan Sebelum & Sesudah Upscale")
                st.caption("Geser garis di tengah gambar ke kanan & kiri untuk melihat perbedaan ketajamannya:")
                image_comparison(
                    img1=original_image,
                    img2=processed_image,
                    label1=f"Asli ({width}x{height})",
                    label2=f"Upscale ({new_width}x{new_height})",
                    width=700
                )

            # 3. MODE EKSEKUSI (MANUAL DOWNLOAD vs AUTO FTP)
            img_byte_arr = io.BytesIO()
            processed_image.save(img_byte_arr, format='JPEG', quality=98)
            img_bytes = img_byte_arr.getvalue()

            if upload_mode == "Manual Upload (Download File)":
                st.markdown("---")
                st.subheader("📥 Download File Hasil Upscale")
                st.download_button(
                    label="💾 Download Gambar (Siap Upload ke Adobe Stock)",
                    data=img_bytes,
                    file_name=f"upscaled_{uploaded_file.name}",
                    mime="image/jpeg",
                    type="primary"
                )

            elif upload_mode == "Auto Upload (FTP Adobe Stock)":
                if not ftp_user or not ftp_pass:
                    st.warning("⚠️ Mode Auto FTP dipilih, namun Username / Password FTP belum diisi!")
                else:
                    with st.spinner("3️⃣ Mengunggah langsung ke FTP Adobe Stock..."):
                        try:
                            ftp = ftplib.FTP(ftp_host)
                            ftp.login(ftp_user, ftp_pass)
                            ftp.storbinary(f'STOR {uploaded_file.name}', io.BytesIO(img_bytes))
                            ftp.quit()

                            st.balloons()
                            st.success(f"🎉 Selesai! File '{uploaded_file.name}' sukses terunggah ke Adobe Stock!")
                        except Exception as e:
                            st.error(f"Gagal upload FTP: {e}")
