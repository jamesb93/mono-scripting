import streamlit as st
import zipfile
from pathlib import Path
import tempfile
from process import process_adv_preset  # assuming this exists

st.title("AMXD Preset Processor")

uploaded_file = st.file_uploader("Upload a ZIP file containing .amxd and .adv files", type="zip")

if uploaded_file:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        extract_path = temp_dir_path / "extracted"
        extract_path.mkdir()
        
        # Save uploaded zip
        zip_path = temp_dir_path / "upload.zip"
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract zip
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_path)

        # Find amxd file
        amxd_files = list(extract_path.rglob("*.amxd"))
        if not amxd_files:
            st.error("No .amxd file found in archive")
            st.stop()
        amxd_path = amxd_files[0]

        st.info(f"Found AMXD file: {amxd_path.name}")

        # Process all .adv files
        adv_files = list(extract_path.rglob("*.adv"))
        if not adv_files:
            st.warning("No .adv files found to process")
            st.stop()

        progress_bar = st.progress(0)
        for idx, adv_file in enumerate(adv_files):
            if "_modified" not in adv_file.stem:
                st.text(f"Processing {adv_file.name}...")
                process_adv_preset(adv_file, amxd_path)
                progress_bar.progress((idx + 1) / len(adv_files))

        # Create output zip
        output_zip = temp_dir_path / "processed.zip"
        with zipfile.ZipFile(output_zip, 'w') as zf:
            for file in extract_path.rglob("*_modified.adv"):
                arcname = file.relative_to(extract_path)
                zf.write(file, arcname)

        # Offer download
        with open(output_zip, 'rb') as f:
            st.download_button(
                label="Download processed presets",
                data=f,
                file_name="processed_presets.zip",
                mime="application/zip"
            )