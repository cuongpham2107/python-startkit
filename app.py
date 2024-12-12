import os
import re
import tempfile
from typing import Literal, Optional, List, Any, Union

from langchain_text_splitters import TextSplitter
import ollama
import streamlit as st
from streamlit_custom_notification_box import custom_notification_box

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from streamlit.runtime.uploaded_file_manager import UploadedFile

# ChromaDB là một cơ sở dữ liệu vector mã nguồn mở dùng để lưu trữ và tìm kiếm các embedding
# OllamaEmbeddingFunction là một hàm tạo embedding sử dụng mô hình Ollama
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction


# Đây là prompt hệ thống được sử dụng để hướng dẫn AI assistant cách trả lời câu hỏi
# Prompt này yêu cầu AI:
# - Chỉ sử dụng thông tin từ context được cung cấp
# - Phân tích kỹ context để tìm thông tin liên quan
# - Tổ chức câu trả lời một cách logic và dễ hiểu
# - Trả lời trực tiếp và đầy đủ câu hỏi
# - Thông báo rõ nếu context không đủ thông tin
# - Sử dụng ngôn ngữ rõ ràng, súc tích
# - Format câu trả lời dễ đọc với đoạn văn, bullet points và headings phù hợp

system_prompt = """
You are an AI assistant tasked with providing detailed answers based solely on the given context. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

context will be passed as "Context:"
user question will be passed as "Question:"

To answer the question:
1. Thoroughly analyze the context, identifying key information relevant to the question.
2. Organize your thoughts and plan your response to ensure a logical flow of information.
3. Formulate a detailed answer that directly addresses the question, using only the information provided in the context.
4. Ensure your answer is comprehensive, covering all relevant aspects found in the context.
5. If the context doesn't contain sufficient information to fully answer the question, state this clearly in your response.

Format your response as follows:
1. Use clear, concise language.
2. Organize your answer into paragraphs for readability.
3. Use bullet points or numbered lists where appropriate to break down complex information.
4. If relevant, include any headings or subheadings to structure your response.
5. Ensure proper grammar, punctuation, and spelling throughout your answer.

Important: Base your entire response solely on the information provided in the context. Do not include any external knowledge or assumptions not present in the given text.
"""

# Upload file
def process_document(uploaded_file: UploadedFile) -> list[Document]:
    # Tạo file tạm thời để lưu nội dung PDF
    temp_file = tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False)
    temp_file.write(uploaded_file.read())
    
    # Sử dụng PyMuPDFLoader để đọc file PDF
    loader = PyMuPDFLoader(temp_file.name)
    docs = loader.load()
    os.unlink(temp_file.name) # Xóa file tạm sau khi đã đọc xong
    
    # Khởi tạo text splitter để chia nhỏ văn bản
    # chunk_size: kích thước mỗi đoạn văn bản
    # chunk_overlap: độ chồng lấp giữa các đoạn
    # separators: các ký tự dùng để tách văn bản
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200, 
        separators=["\n\n", "\n", ".", "?", "!", " ", ""],
        )
    return text_splitter.split_documents(docs)
def get_vector_collection() -> chromadb.Collection:
    ollama_ef = OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text:latest",
    )
    
    
    chroma_client = chromadb.PersistentClient(
        path="./demo-rag-chroma-db"
    )
    return chroma_client.get_or_create_collection(
        name="rag_app",
        embedding_function=ollama_ef,
        metadata={"hnsw:space": "cosine"},
        )
def add_to_vector_collection(all_splits: list[Document], file_name: str):
    collection = get_vector_collection()
    documents, metadatas, ids = [], [], []
    for idx, split in enumerate(all_splits):
        documents.append(split.page_content)
        metadatas.append(split.metadata)
        ids.append(f"{file_name}-{idx}")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        )
    st.success(f"Added {len(all_splits)} documents to vector collection")
def query_collection(prompt: str, n_results:int = 10):
    collection = get_vector_collection()
    results = collection.query(query_texts=[prompt], n_results=n_results)
    return results
def call_llm(context:str, prompt:str):
    response = ollama.chat(
        model="llama3.2:3b",
        stream=True,
        messages= [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Context: {context}, Question: {prompt}"
            }
        ]
    )
    for chunk in response:
        if chunk["done"] is False:
            yield chunk["message"]["content"]
        else:
            break
def re_rank_cross_encoders(documents: list[str]) -> tuple[str, list[int]]:
    relevant_text = ""
    relevant_text_ids = []
    
    encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    ranks = encoder_model.rank(prompt, documents, top_k=3)
    for rank in ranks:
        relevant_text += documents[rank["corpus_id"]]
        relevant_text_ids.append(rank["corpus_id"])
    return relevant_text, relevant_text_ids
if __name__ == "__main__":
    # Tạo sidebar trong Streamlit UI
    with st.sidebar:
        st.set_page_config(page_title="Chat with PDF", page_icon=":books:")
        st.header("🗣️ RAG Question Answering")
        # Tạo widget upload file PDF
        uploaded_file = st.file_uploader(
            "**📖 Upload a PDF file for Question **", type=["pdf"], accept_multiple_files=False
            )
        
        # Tạo nút Process
        process = st.button(
            "**🔍 Process**"
            )
        if __name__ == "__main__":
            # Khi người dùng đã upload file và bấm nút Process
            if uploaded_file and process:
                normalize_uploaded_file_name = uploaded_file.name.translate(
                    str.maketrans({"-": "_", ".":"_", " ": "_"})
                )
                all_splits = process_document(uploaded_file)
                add_to_vector_collection(all_splits, normalize_uploaded_file_name) 
   
    
    
    prompt = st.text_input("**💬 Ask a question about your PDF file:**")
    ask = st.button("**🔍 Ask**")
    
    if ask and prompt:
        results = query_collection(prompt)
        context = results["documents"][0]
        relevant_text, relevant_text_ids = re_rank_cross_encoders(context)
        response = call_llm(relevant_text, prompt)
        st.write_stream(response)
        with st.expander("See retrieved documents"):
            st.write(results)
            
        with st.expander("See most relevant documents ids"):
            st.write(relevant_text_ids)
            st.write(relevant_text)
