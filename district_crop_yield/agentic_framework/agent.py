from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain.schema import StrOutputParser
import json
import sys

import os 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

from agentic_framework.tools import google_search_tool, rag_tool, crop_pred_tool, price_pred_tool
from agentic_framework.prompts import Prompts

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))

load_dotenv(env_path)

prompts = Prompts()

def build_planner_chain(llm, planner_prompt):
    return planner_prompt | llm | StrOutputParser()

def build_answer_chain(llm, answer_prompt):
    return answer_prompt | llm | StrOutputParser()

class Agent():
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # or gemini-1.5-pro
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.tools = {
            "GoogleSearch": google_search_tool,
            "RAG": rag_tool,
            "CropPrediction": crop_pred_tool,
            "PricePrediction": price_pred_tool
        }
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, k=1)
        self.planner_chain = build_planner_chain(self.llm, prompts.planner_prompt)
        self.answer_chain = build_answer_chain(self.llm, prompts.answer_prompt)

    def plan_once(self, query, tool_results):
        history = self.memory.load_memory_variables({})["chat_history"]
        reply = self.planner_chain.invoke({"query": query, "chat_history": history, "tool_results": tool_results})
        self.memory.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_ai_message(reply)
        return reply

    def run(self, query):
        """Full loop: plan → tool execution → stop → final answer."""
        tool_results = {}
        while True:
            # Step 1: Planner
            plan_output = self.plan_once(query, tool_results)

            # Extract JSON safely
            try:
                json_text = plan_output.split("<<<JSON_START>>>")[1].split("<<<JSON_END>>>")[0]
                plan_json = json.loads(json_text)
            except Exception as e:
                raise ValueError(f"Planner output not valid JSON: {plan_output}") from e

            print(f"Plan json ---> {plan_json.get('plan')}")
            # Step 2: Check decision
            for step in plan_json.get("plan", []):
                tool_name = step["tool"]
                action = step["action"]

                # print(f"tool name -> {tool_name}")
                # print(f"action -> {action}")
                # print(f"Step -> {step}")
                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name](action)
                        print(f"Tool {tool_name} executed with action '{action}', result: {result}")
                        print("\n")
                    except Exception as e:
                        result = f"Error running {tool_name} on action '{action}': {e}"
                        print(f"Error occurred: {result} on tool {tool_name}")
                        print("\n")
                else:
                    result = f"Tool {tool_name} not available."

                # Store results under tool_name + action
                tool_results[f"{tool_name}:{action}"] = result

            # Step 3: Execute tools
            if plan_json.get("decision") == "stop":
                # Final step → answer
                # print(f"""
                #     "query": {query},
                #     "chat_history": {self.memory.load_memory_variables({})["chat_history"]},
                #     "tool_results": {tool_results},
                #     "plan": {plan_json}
                # """)
                final_answer = self.answer_chain.invoke({
                    "query": query,
                    "chat_history": self.memory.load_memory_variables({})["chat_history"],
                    "tool_results": tool_results,
                    "final_thought": plan_json.get("final_thought", "")
                })
                # Update history
                self.memory.chat_memory.add_user_message(query)
                self.memory.chat_memory.add_ai_message(final_answer)
                return final_answer

if __name__ == "__main__":
    agent = Agent()
    plan_result = agent.run("What will be the rate of Wheat in Indore for the year 2026?")
    print(f"\n")
    print("planner RESULTS:\n", plan_result)
