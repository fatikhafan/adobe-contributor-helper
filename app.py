import streamlit as st
import ftplib
import os

# Konfigurasi Halaman (Ramah Tampilan HP)
st.set_page_config(
    page_title="Adobe Stock Contributor Helper",
    page_icon="📸",
    layout="centered"
)

st.title("📸 Adobe Contributor Helper")
st.caption("Kelola & Upload Aset Adobe Stock langsung dari HP / Laptop")

# Tab Menu Navigasi Sederhana
tab1, tab2, tab3 = st.tabs(["✍️ Metadata (Tagging)", "🚀 Upload FTP", "⚙️ Pengaturan FTP"])

# --- TAB 1: METADATA / TAGGING ---
with tab1:
    st.subheader("Input Title & Keywords")
    
    uploaded_file = st.file_uploader("Pilih Foto/Video Media", type=['jpg', 'jpeg', 'png', 'mp4'])
    
    title_input = st.text_input("Judul / Deskripsi (Bahasa Inggris):", placeholder="Misal: Fresh green tea leaves in nature")
    keywords_input = st.text_area("Keywords / Tags (Pisahkan dengan koma):", placeholder="green, tea, nature, background, fresh, leaf")
    
    if st.button("Simpan Metadata Local", type="primary"):
        if uploaded_file and title_input:
            st.success(f"✓ Metadata berhasil disiapkan untuk file: {uploaded_file.name}")
            st.json({
                "Nama File": uploaded_file.name,
                "Title": title_input,
                "Keywords": [k.strip() for k in keywords_input.split(',')]
            })
        else:
            st.warning("Mohon upload file dan isi judul terlebih dahulu!")

# --- TAB 2: UPLOAD FTP ---
with tab2:
    st.subheader("Upload ke Server Adobe Stock")
    
    # Cek Kredensial FTP dari Session State
    ftp_host = st.session_state.get('ftp_host', 'ftp.stock.adobe.com')
    ftp_user = st.session_state.get('ftp_user', '')
    ftp_pass = st.session_state.get('ftp_pass', '')

    file_to_upload = st.file_uploader("Pilih File yang Siap Diunggah", type=['jpg', 'jpeg', 'png', 'mp4'], key="upload_ftp")
    
    if st.button("🚀 Mulai Upload ke Adobe Stock"):
        if not ftp_user or not ftp_pass:
            st.error("Silakan atur Username & Password FTP di tab 'Pengaturan FTP' terlebih dahulu!")
        elif not file_to_upload:
            st.warning("Pilih file yang ingin di-upload!")
        else:
            try:
                with st.spinner(f"Mengunggah {file_to_upload.name} ke Adobe Stock FTP..."):
                    # Simpan file temporary lokal untuk proses upload
                    temp_path = os.path.join("temp_" + file_to_upload.name)
                    with open(temp_path, "wb") as f:
                        f.write(file_to_upload.getbuffer())

                    # Koneksi & Upload FTP
                    ftp = ftplib.FTP(ftp_host)
                    ftp.login(ftp_user, ftp_pass)
                    
                    with open(temp_path, 'rb') as f:
                        ftp.storbinary(f'STOR {file_to_upload.name}', f)
                    ftp.quit()

                    # Hapus file temporary
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                st.success(f"🎉 Berhasil diunggah ke Adobe Stock: {file_to_upload.name}")
            except Exception as e:
                st.error(f"Gagal melakukan upload FTP: {e}")

# --- TAB 3: PENGATURAN FTP ---
with tab3:
    st.subheader("Kredensial FTP Adobe Stock")
    st.info("Dapatkan Username & Password FTP dari dasbor Adobe Stock Contributor Anda.")
    
    host = st.text_input("FTP Host", value="ftp.stock.adobe.com")
    user = st.text_input("FTP Username", value=st.session_state.get('ftp_user', ''))
    password = st.text_input("FTP Password", type="password", value=st.session_state.get('ftp_pass', ''))
    
    if st.button("Simpan Pengaturan"):
        st.session_state['ftp_host'] = host
        st.session_state['ftp_user'] = user
        st.session_state['ftp_pass'] = password
        st.success("✓ Kredensial FTP berhasil disimpan di sesi ini!")