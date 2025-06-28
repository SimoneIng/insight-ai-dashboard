import streamlit as st
import os
import pandas as pd
import plotly.express as px
import json
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import CTransformers
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# --- CONFIGURAZIONE INIZIALE ---

# Cache per ottimizzare le prestazioni
@st.cache_resource
def load_embedding_model():
    """Carica il modello di embedding una sola volta."""
    return HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})

@st.cache_resource
def load_llm_model(model_path):
    """Carica il modello LLM locale una sola volta."""
    # Assicurati che il percorso al modello .gguf sia corretto
    if not os.path.exists(model_path):
        st.error(f"Modello non trovato in {model_path}. Scaricalo e posizionalo correttamente.")
        return None
    return CTransformers(
        model=model_path,
        model_type='mistral', # Cambia in 'llama' se usi un modello Llama
        config={'max_new_tokens': 512, 'temperature': 0.1, 'context_length': 4096}
    )

# --- FUNZIONI DI LOGICA ---

def load_documents_from_folder(folder_path):
    """Carica i documenti da una cartella, supportando .pdf, .docx, .md."""
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".docx"):
                loader = UnstructuredWordDocumentLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".md"):
                loader = UnstructuredMarkdownLoader(file_path)
                documents.extend(loader.load())
        except Exception as e:
            st.warning(f"Errore nel caricamento del file {filename}: {e}")
    return documents

def create_vector_store(documents, embedding_model):
    """Crea un vector store FAISS a partire dai documenti."""
    if not documents:
        return None
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    vector_store = FAISS.from_documents(texts, embedding_model)
    return vector_store

# Questo è il prompt "magico" che istruisce il modello a generare JSON
prompt_template = """
Usa le seguenti informazioni di contesto per rispondere alla domanda.
Il tuo obiettivo è estrarre i dati richiesti e formattarli per creare un grafico.

Contesto: {context}

Domanda: {question}

Risposta: Fornisci una risposta in formato JSON valido. Il JSON deve avere due chiavi:
1. "summary": una breve frase che riassume la risposta.
2. "chart_data": un array di oggetti, dove ogni oggetto rappresenta un punto dati.
   Ad esempio: [{"label": "Gennaio", "value": 150}, {"label": "Febbraio", "value": 200}]

Se non riesci a trovare dati numerici per un grafico, la chiave "chart_data" deve essere un array vuoto.

Risposta JSON:
"""

PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# --- INTERFACCIA STREAMLIT ---

st.set_page_config(layout="wide")
st.title("📊 Dashboard di Analisi Documenti con LLM Locale")
st.markdown("Seleziona una cartella, fai una domanda in linguaggio naturale e ottieni un'analisi visuale.")

# Caricamento modelli con messaggi di stato
with st.spinner("Caricamento modelli di embedding e LLM... (potrebbe richiedere tempo la prima volta)"):
    embeddings = load_embedding_model()
    # Inserisci qui il percorso al tuo modello .gguf scaricato
    llm = load_llm_model('Llama-3.2-3B-Instruct-IQ3_M.gguf') 

if llm is None:
    st.stop()

# Input dell'utente
folder_path = st.text_input("Inserisci il percorso completo della cartella contenente i tuoi file:", placeholder="Es. /Users/nome/Documenti")
query = st.text_input("Scrivi la tua query:", placeholder="Es. Mostrami le vendite mensili del prodotto X nel 2024")

if st.button("Analizza e Genera Grafico"):
    if not folder_path or not os.path.isdir(folder_path):
        st.error("Per favore, inserisci un percorso di cartella valido.")
    elif not query:
        st.error("Per favore, inserisci una query.")
    else:
        try:
            # 1. Caricamento Documenti
            with st.spinner(f"Caricamento file dalla cartella: {folder_path}..."):
                docs = load_documents_from_folder(folder_path)
            
            if not docs:
                st.warning("Nessun file supportato (.pdf, .docx, .md) trovato nella cartella.")
            else:
                # 2. Creazione Vector Store
                with st.spinner("Creazione dell'indice semantico (Vector Store)..."):
                    vector_store = create_vector_store(docs, embeddings)

                # 3. Creazione della Retrieval Chain
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=vector_store.as_retriever(),
                    chain_type_kwargs={"prompt": PROMPT},
                    return_source_documents=True
                )

                # 4. Esecuzione della Query
                with st.spinner("Il modello sta pensando..."):
                    response = qa_chain.invoke(query)
                    result_text = response['result']

                st.subheader("Risultati dell'Analisi")

                # 5. Parsing della risposta JSON e creazione grafico
                try:
                    data = json.loads(result_text)
                    summary = data.get("summary", "Nessun riassunto fornito.")
                    chart_data = data.get("chart_data", [])

                    st.markdown(f"**Riassunto:** {summary}")

                    if chart_data and isinstance(chart_data, list) and len(chart_data) > 0:
                        df = pd.DataFrame(chart_data)
                        
                        # Controllo delle colonne necessarie
                        if "label" in df.columns and "value" in df.columns:
                            st.write("Dati estratti:", df)
                            fig = px.bar(df, x='label', y='value', title=f"Visualizzazione per: '{query}'")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Il modello ha restituito dati ma mancano le colonne 'label' o 'value'.")
                            st.json(chart_data)

                    else:
                        st.info("Non è stato possibile estrarre dati sufficienti per generare un grafico.")
                        st.write("Risposta testuale del modello:", result_text)

                except json.JSONDecodeError:
                    st.error("Il modello non ha restituito un JSON valido. Impossibile generare il grafico.")
                    st.write("Risposta grezza del modello:")
                    st.code(result_text)

        except Exception as e:
            st.error(f"Si è verificato un errore durante l'analisi: {e}")