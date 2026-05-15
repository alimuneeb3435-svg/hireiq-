from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    temperature=0.3,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

vector_store = None

def setup_rag():
    global vector_store
    try:
        kb_path = "data/company_knowledge.txt"
        if not os.path.exists(kb_path):
            print(f"Knowledge base not found at {kb_path}")
            return None
        loader = TextLoader(kb_path, encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="./data/chroma_db"
        )
        vector_store.persist()
        print("RAG setup complete!")
        return vector_store
    except Exception as e:
        print(f"Error setting up RAG: {e}")
        return None

def get_rag_answer(question: str) -> str:
    global vector_store
    if vector_store is None:
        setup_rag()
    if vector_store is None:
        try:
            with open("data/company_knowledge.txt", "r", encoding="utf-8") as f:
                content = f.read()
            return content[:2000]
        except:
            return "Company information temporarily unavailable."
    try:
        docs = vector_store.similarity_search(question, k=5)
        if not docs:
            return "I could not find specific information about that."
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"""You are a helpful assistant for TechNova Solutions.
Answer the user's question based ONLY on the following company information:

{context}

User Question: {question}

STRICT RULES:
- If the answer exists above, answer it DIRECTLY and COMPLETELY
- Never say I do not have information if the context contains the answer
- Never redirect to email if the answer is already in the context
- Only suggest contacting info@technovasolutions.pk if genuinely not found"""
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error getting RAG answer: {e}")
        return "I am having trouble accessing company information right now."
