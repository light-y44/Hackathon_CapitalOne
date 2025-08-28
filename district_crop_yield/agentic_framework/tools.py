from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os
import sys
import requests 
from langchain.tools import StructuredTool


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

from utils.utils import calculateYieldPred_Tool_structured, calculatePricePredTool

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
  ans = "\n".join([doc.page_content for doc in vectorstore.similarity_search(query, k=1)])
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

crop_pred_tool = StructuredTool.from_function(
    name="CropPrediction",
    func=calculateYieldPred_Tool_structured,
    description="Predict crop yields based on weather and indices data.",
)

price_pred_tool = Tool(
    name="PricePrediction",
    func=calculatePricePredTool,
    description="Predict crop prices based on historical data."
)

import requests

def getFinancials(_: str) -> str:
    """
    Calls the backend API to fetch financial recommendations.
    Input is ignored (underscore) since the endpoint requires none.
    """
    url = "http://127.0.0.1:5000/api/get_financial_details"
    try:
        resp = requests.get(url)  # adjust port if needed
        resp.raise_for_status()
        data = resp.json()
        return str(data)  # return as string for the agent
    except Exception as e:
        return f"Error fetching financial details: {e}"


get_financial_tool = Tool(
    name="GetFinancialAdvice",
    func=getFinancials,
    description="Get financial advice based on market trends and crop data."
)

if __name__ == "__main__":
    input = "What financial advice can you give to a farmer in Punjab growing wheat with 5 hectares of land?"
    print(get_financial_tool.run(input))