import streamlit as st
import ftplib
import os
import google.generativeai as genai
from PIL import Image
from streamlit_image_comparison import image_comparison

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Adobe Stock Contributor Helper - Auto Pipeline",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ Adobe Contributor All-in-One Auto")
st.caption("Upload gambar -> Auto AI Title & Keywords -> Auto Upscale (Slider) -> Auto FTP Upload")

# --- AKSES API KEY & FTP DARI SIDEBAR / SETTINGS ---
st.sidebar.header("⚙️ Konfigurasi")
gemini_api_key = st.sidebar.text_input("Gemini AI API Key", type="password", help="Masukkan API Key Google Gemini")
ftp_host = st.sidebar.text_input("FTP Host", value="ftp.stock.adobe.com")
ftp_user = st.sidebar.text_input("FTP Username", value=st.session_state.get('ftp_user', ''))
ftp_pass = st.sidebar.text_input("FTP Password", type="password", value=st.session_state.get('ftp_pass', ''))

if st.sidebar.button("Simpan Konfigurasi"):
    st.session_state['ftp_user'] = ftp_user
    st.session_state['ftp_pass'] = ftp_pass
    st.sidebar.success("Konfigurasi disimpan!")

st.markdown("---")

# --- AREA UTAMA: ALL-IN-ONE AUTOMATION ---
uploaded_file = st.file_uploader("📸 Upload Foto / Gambar di Sini", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    width, height = original_image.size
    st.info(f"📐 Resolusi Asli: {width} x {height} piksel")

    # Pilihan Opsional
    enable_upscale = st.checkbox("Perbesar Resolusi (Upscale 2x/4x)", value=True)
    auto_upload_ftp = st.checkbox("Otomatis Upload ke Adobe Stock FTP setelah selesai", value=True)

    if st.button("🚀 Jalankan Proses Otomatis (Auto Magic)", type="primary"):
        processed_image = original_image.copy()

        # 1. AI METADATA GENERATION
        if not gemini_api_key:
            st.error("Harap isi Gemini AI API Key di menu Konfigurasi sebelah kiri!")
        else:
            with st.spinner("1️⃣ Menganalisis gambar menggunakan AI..."):
                try:
                    genai.configure(api_key=gemini_api_key)
                    # Menggunakan model terupdate agar tidak error 404
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')

                    prompt = """
                    Analyze this image for Adobe Stock Contributor submission.
                    Provide output in this EXACT format:
                    Title: <English title describing the image, max 10 words>
                    Keywords: <30 English keywords separated by commas>
                    """
                    
                    response = model.generate_content([prompt, original_image])
                    st.success("✓ AI Berhasil Generate Title & Keywords!")
                    st.text_area("Hasil AI Metadata:", value=response.text, height=120)

                except Exception as e:
                    # Fallback ke model versi 1.5 jika flash-latest berhalangan
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        response = model.generate_content([prompt, original_image])
                        st.success("✓ AI Berhasil Generate Title & Keywords!")
                        st.text_area("Hasil AI Metadata:", value=response.text, height=120)
                    except Exception as err:
                        st.error(f"Gagal generate AI Metadata: {err}")

        # 2. PROSES UPSCALE & COMPARE SLIDER
        if enable_upscale:
            with st.spinner("2️⃣ Memperbesar resolusi gambar..."):
                new_width, new_height = width * 2, height * 2
                processed_image = original_image.resize((new_width, new_height), Image.LANCZOS)
                st.success(f"✓ Resolusi berhasil dinaikkan menjadi {new_width} x {new_height} piksel")
                
                # TAMPILKAN SLIDER PERBANDINGAN (GESER KANAN-KIRI)
                st.subheader("🔍 Perbandingan Sebelum & Sesudah Upscale")
                st.caption("Geser garis di tengah gambar ke kanan & kiri untuk membandingkan hasil!")
                image_comparison(
                    img1=original_image,
                    img2=processed_image,
                    label1="Asli (Sebelum)",
                    label2="Upscale (Sesudah)",
                    width=700
                )

        # 3. PROSES FTP UPLOAD
        if auto_upload_ftp:
            temp_filename = f"processed_{uploaded_file.name}"
            processed_image.save(temp_filename, quality=95)

            if not ftp_user or not ftp_pass:
                st.warning("⚠️ Username atau Password FTP belum diisi di menu Konfigurasi. File siap tapi belum diunggah.")
            else:
                with st.spinner("3️⃣ Mengunggah langsung ke Adobe Stock FTP..."):
                    try:
                        ftp = ftplib.FTP(ftp_host)
                        ftp.login(ftp_user, ftp_pass)
                        
                        with open(temp_filename, 'rb') as f:
                            ftp.storbinary(f'STOR {uploaded_file.name}', f)
                        ftp.quit()

                        st.balloons()
                        st.success(f"🎉 Selesai! File '{uploaded_file.name}' sukses terunggah ke Adobe Stock!")
                    except Exception as e:
                        st.error(f"Gagal upload FTP: {e}")

            if os.path.exists(temp_filename):
                os.remove(temp_filename)
