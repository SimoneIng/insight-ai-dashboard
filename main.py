import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Demo Dashboard", layout="centered")

# Titolo dell'app
st.title("Demo Dashboard")

# Selettore cartella (simulato)
folder = st.text_input("1. Inserisci il percorso della cartella con i documenti (simulato)", "/path/to/docs")
st.write(f"Cartella selezionata: {folder}")

# Input di query in linguaggio naturale
query = st.text_input("2. Digita la tua query (es. 'Mostra l'andamento degli stipendi nel tempo')")

# Bottone per generare
if st.button("Conferma e genera"):
    # Funzione fake LLM per generare dati finti
    def fake_llm_response(query_text):
        if query_text == "":
            return {"warning": "Query vuota. Scrivi cosa vuoi analizzare."}

        # Se la query contiene 'stipendi'
        elif "stipendi" in query_text.lower():
            dates = [datetime.now() - timedelta(days=30*i) for i in range(12)][::-1]
            values = np.random.randint(2000, 5000, size=12)
            return {
                "chart_type": "line",
                "title": "Andamento stipendi",
                "x": [d.strftime('%Y-%m') for d in dates],
                "y": values.tolist()
            }
        # Se la query contiene 'vendite'
        elif "vendite" in query_text.lower():
            quarters = [f"Q{i}" for i in range(1,5)]
            values = np.random.randint(10000, 50000, size=4)
            return {
                "chart_type": "bar",
                "title": "Vendite per trimestre",
                "x": quarters,
                "y": values.tolist()
            }
        # Altrimenti ritorna errore
        else:
            return {"error": "Non ci sono dati sufficienti per costruire un grafico o una tabella."}

    # Chiamata fake LLM
    response = fake_llm_response(query)

    # Gestione risposta
    if "warning" in response:
        st.warning(response["warning"])
    elif "error" in response:
        st.error(response["error"])
    else:
        chart_type = response["chart_type"]
        title = response["title"]
        x = response.get("x", [])
        y = response.get("y", [])

        st.subheader(title)

        df = pd.DataFrame({"x": x, "y": y})
        df = df.set_index("x")

        if chart_type == "line":
            st.line_chart(df)
        elif chart_type == "bar":
            st.bar_chart(df)
        elif chart_type == "pie":
            # per demo, st.pyplot con matplotlib
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.pie(response.get("values", []), labels=response.get("labels", []), autopct='%1.1f%%')
            st.pyplot(fig)
        elif chart_type == "table":
            st.table(response.get("table", []))
        else:
            st.write("Tipo di grafico non supportato nella demo.")
