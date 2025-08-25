from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


from dotenv import load_dotenv
import os

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))

load_dotenv(env_path)

OUTPUT_VDB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../rag/faiss"))


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = FAISS.load_local(OUTPUT_VDB_PATH, embeddings, allow_dangerous_deserialization=True)

serper = GoogleSerperAPIWrapper(serper_api_key = os.getenv("SERPER_API_KEY"))

# wrap it as a Tool for your planner
google_search_tool = Tool(
    name="GoogleSearch",
    func=serper.run,
    description="Useful for answering questions about current events or factual knowledge"
)

def get_doc_using_rag(query):
  ans = "\n".join([doc.page_content for doc in vectorstore.similarity_search(query, k=3)])
  return ans

rag_tool = Tool(
    name="RAG",
    func=get_doc_using_rag,
    description=(
        "Use this to retrieve relevant information from the uploaded documents. "
        "Input: a natural language question (string). "
        "Output: up to 3 relevant passages of text concatenated together."
    )
)


if __name__ == "__main__":
    query = "what is the best fertilizer for wheat?"
    print(rag_tool(query))