from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
from dotenv import load_dotenv
import os

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))

load_dotenv(env_path)


serper = GoogleSerperAPIWrapper(serper_api_key = os.getenv("SERPER_API_KEY"))

# wrap it as a Tool for your planner
google_search_tool = Tool(
    name="GoogleSearch",
    func=serper.run,
    description="Useful for answering questions about current events or factual knowledge"
)

