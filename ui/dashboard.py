import streamlit as st
import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Configurazione cartelle
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # root del progetto
DOCS_DIR = BASE_DIR / "data" / "raw"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Configurazione pagina
# -----------------------------------------------------------------------------
st.set_page_config(page_title="TechVisory AI Insights Platform", layout="wide")
st.title("TechVisory AI Insights Platform")

st.markdown(
    """Scrivi una query in linguaggio naturale per ottenere insight dai documenti contrattuali.\n"""
)

# -----------------------------------------------------------------------------
# SIDEBAR – Upload e visualizzazione documenti
# -----------------------------------------------------------------------------
st.sidebar.header("Documenti")

uploaded_files = st.sidebar.file_uploader(
    label="Carica uno o più documenti",
    type=["pdf", "docx", "md"],
    accept_multiple_files=True,
    help="Sono supportati PDF, DOCX e Markdown. I file caricati verranno salvati in data/raw."
)

if uploaded_files:
    saved_files = []
    for up_file in uploaded_files:
        save_path = DOCS_DIR / up_file.name
        if save_path.exists():
            base, ext = os.path.splitext(up_file.name)
            i = 1
            while (DOCS_DIR / f"{base}_{i}{ext}").exists():
                i += 1
            save_path = DOCS_DIR / f"{base}_{i}{ext}"
        with open(save_path, "wb") as f:
            f.write(up_file.getbuffer())
        saved_files.append(save_path.name)

    st.sidebar.success(f"{len(saved_files)} file salvati correttamente.")

with st.sidebar.expander("Documenti nella knowledge base", expanded=False):
    files = sorted(p.name for p in DOCS_DIR.glob("*"))
    if files:
        st.sidebar.write("\n".join(files))
    else:
        st.sidebar.info("Nessun documento presente.")

# -----------------------------------------------------------------------------
# QUERY – Area principale
# -----------------------------------------------------------------------------
query = st.text_input("Scrivi la tua query (es. 'Mostrami i contratti con scadenza entro 3 mesi'):")

if query:
    if st.button("Esegui query"):
        st.info("⏳ Esecuzione query in corso… (funzionalità in fase di sviluppo)")
        st.warning("Funzionalità di risposta non ancora implementata. Prossimamente qui comparirà il risultato della query.")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("© 2025 Techvisory – Prototype. Tutti i diritti riservati.")

