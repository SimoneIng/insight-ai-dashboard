import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Configurazione iniziale della pagina
st.set_page_config(
    page_title="Demo Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === SIDEBAR ===
st.sidebar.title("📁 Carica i tuoi documenti")

# Simulazione di sottocartelle
folders = [
    "Contratti commerciali",  # default
    "Fatture",
    "Report mensili",
    "Comunicazioni",
    "Altro"
]

selected_folder = st.sidebar.selectbox(
    "Scegli una sottocartella:",
    folders,
    index=folders.index("Contratti commerciali")
)

st.sidebar.write(f"📂 Cartella selezionata: **{selected_folder}**")

# Simulazione di caricamento file in base alla cartella selezionata
uploaded_files = st.sidebar.file_uploader(
    f"Carica file in '{selected_folder}'",
    type=["pdf", "csv", "txt", "docx"],
    accept_multiple_files=True
)

if uploaded_files:
    st.sidebar.success(f"{len(uploaded_files)} file caricati.")
else:
    st.sidebar.info("Nessun file caricato in questa cartella.")

# === CONTENUTO PRINCIPALE ===
st.title("📊 Search Driven Analytics")


# Input utente
query = st.text_input("✏️ Digita la tua query", placeholder="Es. Mostra l'andamento degli stipendi nel tempo")

# Bottone
if st.button("🎯 Conferma e genera"):
    
    def fake_llm_response(query_text):
        if query_text.strip() == "":
            return {"warning": "Query vuota. Scrivi cosa vuoi analizzare."}
        elif "stipendi" in query_text.lower():
            dates = [datetime.now() - timedelta(days=30*i) for i in range(12)][::-1]
            values = np.random.randint(2000, 5000, size=12)
            return {
                "chart_type": "line",
                "title": "Andamento degli stipendi negli ultimi 12 mesi",
                "x": [d.strftime('%Y-%m') for d in dates],
                "y": values.tolist()
            }
        elif "vendite" in query_text.lower():
            quarters = [f"Q{i}" for i in range(1,5)]
            values = np.random.randint(10000, 50000, size=4)
            return {
                "chart_type": "bar",
                "title": "Vendite per trimestre",
                "x": quarters,
                "y": values.tolist()
            }
        else:
            return {"error": "Non ci sono dati sufficienti per costruire un grafico o una tabella."}

    # Risposta simulata
    response = fake_llm_response(query)

    # Output
    if "warning" in response:
        st.warning(response["warning"])
    elif "error" in response:
        st.error(response["error"])
    else:
        chart_type = response["chart_type"]
        title = response["title"]
        x = response.get("x", [])
        y = response.get("y", [])

        st.subheader(f"📈 {title}")

        df = pd.DataFrame({"x": x, "y": y}).set_index("x")

        if chart_type == "line":
            st.line_chart(df)
        elif chart_type == "bar":
            st.bar_chart(df)
        elif chart_type == "pie":
            fig, ax = plt.subplots()
            ax.pie(response.get("values", []), labels=response.get("labels", []), autopct='%1.1f%%')
            st.pyplot(fig)
        elif chart_type == "table":
            st.table(response.get("table", []))
        else:
            st.info("Tipo di grafico non supportato nella demo.")
