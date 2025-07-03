import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import requests
from typing import Dict, Any, Optional


# Configurazione della pagina
st.set_page_config(page_title="LLM Chart Generator", page_icon="📊", layout="wide")


def get_text_files_from_folder(folder_path: str) -> Dict[str, str]:
    """Legge tutti i file di testo dalla cartella selezionata"""
    text_files = {}
    if not folder_path or not os.path.exists(folder_path):
        return text_files

    try:
        for file_path in Path(folder_path).rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".txt", ".md", ".csv"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        text_files[str(file_path)] = content
                except Exception as e:
                    st.warning(f"Impossibile leggere il file {file_path}: {str(e)}")
    except Exception as e:
        st.error(f"Errore nella lettura della cartella: {str(e)}")

    return text_files


def call_local_llm(
    prompt: str,
    llm_url: str = "http://localhost:11434/api/generate",
    model: str = "deepseek-r1",
) -> Optional[Dict[str, Any]]:
    """Chiama un LLM (es. Ollama) con il prompt fornito"""
    try:
        # Configurazione per Ollama (modifica secondo il tuo setup)
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": 0, # non tiene traccia del contesto
        }

        response = requests.post(llm_url, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "").strip()

            # Prova a parsare la risposta JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Se la risposta non è JSON valido, prova a estrarre il JSON
                import re

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"error": "Risposta del LLM non in formato JSON valido"}
        else:
            return {"error": f"Errore nella chiamata al LLM: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Errore di connessione al LLM: {str(e)}"}
    except Exception as e:
        return {"error": f"Errore generico: {str(e)}"}


def create_chart(chart_data: Dict[str, Any]) -> Optional[go.Figure]:
    """Crea il grafico basato sui dati ricevuti dal LLM"""
    print(chart_data)
    try:
        chart_type = chart_data.get("chart_type", "").lower()
        title = chart_data.get("title", "Grafico Generato")

        if chart_type == "bar":
            x_values = chart_data.get("x", [])
            y_values = chart_data.get("y", [])
            fig = px.bar(x=x_values, y=y_values, title=title)

        elif chart_type == "line":
            x_values = chart_data.get("x", [])
            y_values = chart_data.get("y", [])
            fig = px.line(x=x_values, y=y_values, title=title)

        elif chart_type == "pie":
            labels = chart_data.get("labels", [])
            values = chart_data.get("values", [])
            fig = px.pie(values=values, names=labels, title=title)

        elif chart_type == "scatter":
            x_values = chart_data.get("x", [])
            y_values = chart_data.get("y", [])
            fig = px.scatter(x=x_values, y=y_values, title=title)

        elif chart_type == "table":
            table_data = chart_data.get("table", [])
            if table_data:
                df = pd.DataFrame(table_data)
                st.subheader(title)
                st.dataframe(df, use_container_width=True)
                return None
            else:
                return None
        else:
            return None

        return fig

    except Exception as e:
        st.error(f"Errore nella creazione del grafico: {str(e)}")
        return None


# Interface principale
st.title("📊 LLM Chart Generator")
st.markdown("Genera grafici e tabelle da testi utilizzando un LLM")

# Sidebar per configurazioni
with st.sidebar:
    st.header("⚙️ Configurazioni")

    # URL del LLM
    llm_url = st.text_input(
        "URL LLM",
        value="http://localhost:11434/api/generate",
        help="URL del tuo LLM (es. Ollama)",
    )

    # Modello da utilizzare
    model_name = st.text_input(
        "Nome Modello",
        value="deepseek-r1",
        help="Nome del modello da utilizzare",
    )

    st.markdown("---")
    st.markdown("**Come usare:**")
    st.markdown("1. Seleziona una cartella con file di testo")
    st.markdown("2. Inserisci la tua richiesta")
    st.markdown("3. Scegli un file da analizzare")
    st.markdown("4. Clicca 'Genera Grafico'")

# Selezione cartella
st.header("📁 Selezione Cartella")
folder_path = st.text_input(
    "Percorso della cartella:",
    placeholder="es. /percorso/alla/tua/cartella",
    help="Inserisci il percorso completo della cartella contenente i file di testo",
)

# Caricamento file dalla cartella
if folder_path:
    text_files = get_text_files_from_folder(folder_path)

    if text_files:
        st.success(f"Trovati {len(text_files)} file di testo nella cartella")

        # Selezione file
        selected_file = st.selectbox("Seleziona un file da analizzare:", options=list(text_files.keys()), format_func=lambda x: os.path.basename(x))

        # Mostra anteprima del file selezionato
        if selected_file:
            with st.expander("📄 Anteprima del file selezionato"):
                content_preview = text_files[selected_file][:1000]
                if len(text_files[selected_file]) > 1000:
                    content_preview += "..."
                st.text_area("Contenuto:", content_preview, height=200, disabled=True)

        # Input richiesta utente
        st.header("💬 Richiesta")
        user_query = st.text_area(
            "Cosa vuoi estrarre/visualizzare dai dati?",
            placeholder="es. Crea un grafico a barre delle vendite per mese",
            value="Voglio sapere l'andamento degli stipendi nel tempo",
            height=100,
        )

        # Pulsante per generare il grafico
        if st.button("🚀 Genera Grafico", type="primary"):
            if not user_query.strip():
                st.error("Inserisci una richiesta!")
            elif not selected_file:
                st.error("Seleziona un file!")
            else:
                with st.spinner("Elaborazione in corso..."):
                    # Costruzione del prompt
                    prompt_template = """
Sei un assistente specializzato nell'estrazione e visualizzazione di dati. Il tuo compito è analizzare il testo fornito ed estrarre dati per creare visualizzazioni.

## ISTRUZIONI CRITICHE:
1. Rispondi SOLO con JSON valido, senza testo aggiuntivo
2. Usa ESATTAMENTE i nomi dei campi specificati negli schemi
3. Non aggiungere, rimuovere o modificare i nomi dei campi
4. le liste "x" e "y" devono avere la stessa quantità di valori

## SCHEMI JSON (USA ESATTAMENTE QUESTI):

### Per grafici a barre o a linee:
```json
{{
    "chart_type": "bar",
    "title": "string",
    "x": ["array di stringhe"],
    "y": ["array di numeri"]
}}
```

### Per grafici a torta:
```json
{{
    "chart_type": "pie", 
    "title": "string",
    "labels": ["array di stringhe"],
    "values": ["array di numeri"]
}}
```

### Per scatter plot:
```json
{{
    "chart_type": "scatter",
    "title": "string", 
    "x": ["array di numeri"],
    "y": ["array di numeri"],
    "point_labels": ["array di stringhe (opzionale)"]
}}
```

### Per tabelle:
```json
{{
    "chart_type": "table",
    "title": "string",
    "headers": ["array di stringhe"],
    "rows": [["array", "di", "valori"], ["seconda", "riga", "valori"]]
}}
```

### Per errori:
```json
{{
    "error": "Messaggio di errore specifico"
}}
```

## REGOLE DI SELEZIONE TIPO GRAFICO:
- **bar**: Confronti tra categorie, ranking, quantità discrete
- **line**: Trend temporali, progressioni, evoluzioni
- **pie**: Composizione percentuale, parti di un tutto
- **scatter**: Correlazioni tra due variabili numeriche
- **table**: Dati complessi multicolonna o liste dettagliate

## VALIDAZIONE OUTPUT:
Prima di rispondere, verifica:
1. Il JSON è sintatticamente corretto
2. I nomi dei campi corrispondono ESATTAMENTE agli schemi
3. I tipi di dati sono corretti (stringhe, numeri, array)
4. Non ci sono campi extra o mancanti

---

**Richiesta utente:** {query}

**Testo da analizzare:** {text}

**RISPOSTA (solo JSON)**
"""

                    full_prompt = prompt_template.format(query=user_query, text=text_files[selected_file])

                    # Chiamata al LLM
                    result = call_local_llm(full_prompt, llm_url, model_name)

                    if result:
                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            # Mostra i dati estratti
                            with st.expander("📊 Dati estratti dal LLM"):
                                st.json(result)

                            # Crea e mostra il grafico
                            fig = create_chart(result)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)

                                # Pulsante per scaricare i dati
                                if st.button("💾 Scarica dati JSON"):
                                    st.download_button(
                                        label="Scarica JSON", data=json.dumps(result, indent=2), file_name="chart_data.json", mime="application/json"
                                    )
                    else:
                        st.error("❌ Errore nella comunicazione con il LLM")

    else:
        st.warning("⚠️ Nessun file di testo trovato nella cartella specificata")
else:
    st.info("👆 Inserisci il percorso di una cartella per iniziare")

# Footer
st.markdown("---")
st.markdown("**Nota:** Assicurati che il tuo LLM sia in esecuzione e accessibile all'URL specificato.")
