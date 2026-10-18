import streamlit as st
import ftplib
import os
import google.generativeai as genai
from PIL import Image

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Adobe Stock Contributor Helper - Auto Pipeline",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ Adobe Contributor All-in-One Auto")
st.caption("Upload gambar -> Auto AI Title & Keywords -> Auto Upload ke Adobe Stock FTP")

# --- AKSES API KEY & FTP DARI SIDEBAR / SETTINGS ---
st.sidebar.header("⚙️ Konfigurasi")
gemini_api_key = st.sidebar.text_input("Gemini AI API Key", type="password", help="Masukkan API Key Google Gemini gratisan untuk AI auto-tagging")
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
    # Tampilkan Preview Gambar
    image = Image.open(uploaded_file)
    st.image(image, caption=f"File: {uploaded_file.name}", use_column_width=True)

    # Cek Resolusi Gambar saat ini
    width, height = image.size
    st.info(f"📐 Resolusi Asli: {width} x {height} piksel")

    # Pilihan Upscale & Auto Process
    enable_upscale = st.checkbox("Perbesar Resolusi (Upscale 2x/4x)", value=True)
    auto_upload_ftp = st.checkbox("Otomatis Upload ke Adobe Stock FTP setelah selesai", value=True)

    if st.button("🚀 Jalankan Proses Otomatis (Auto Magic)", type="primary"):
        if not gemini_api_key:
            st.error("Harap isi Gemini AI API Key di menu Konfigurasi sebelah kiri!")
        else:
            with st.spinner("1️⃣ Menganalisis gambar menggunakan AI..."):
                try:
                    # Konfigurasi Gemini API
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')

                    prompt = """
                    Analyze this image for Adobe Stock Contributor submission.
                    Provide output in this EXACT JSON-like format:
                    Title: <English title describing the image, max 10 words>
                    Keywords: <30 English keywords separated by commas>
                    """
                    
                    response = model.generate_content([prompt, image])
                    ai_text = response.text
                    
                    st.success("✓ AI Berhasil Generate Title & Keywords!")
                    st.text_area("Hasil AI Metadata:", value=ai_text, height=120)

                except Exception as e:
                    st.error(f"Gagal generate AI Metadata: {e}")
                    ai_text = None

            # Proses Upscale (resize canvas jika di cloud)
            if enable_upscale:
                with st.spinner("2️⃣ Memperbesar resolusi gambar..."):
                    new_width, new_height = width * 2, height * 2
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                    st.success(f"✓ Resolusi berhasil dinaikkan menjadi {new_width} x {new_height} piksel")

            # Simpan file sementara
            temp_filename = f"processed_{uploaded_file.name}"
            image.save(temp_filename, quality=95)

            # Proses FTP Upload
            if auto_upload_ftp:
                if not ftp_user or not ftp_pass:
                    st.error("⚠️ Username atau Password FTP belum diisi di menu Konfigurasi!")
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

            # Cleanup file sementara
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
