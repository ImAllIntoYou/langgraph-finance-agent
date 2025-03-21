import os
from typing import Annotated, TypedDict 
from dotenv import load_dotenv

from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import StateGraph, END


# Load environment variables from .env file
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")


llm_name = "gemini-2.0-pro-exp-02-05"

client = genai.Client(api_key=gemini_key)
model = ChatGoogleGenerativeAI(api_key=gemini_key, model="gemini-2.0-pro-exp-02-05")


# Step 1: Build a basic Chatbot
from langgraph.graph.message import add_messages


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overriding them)
    messages: Annotated[list, add_messages]


def bot(state: State):
    # print(state.items())
    print(state["messages"])
    return {"messages": [model.invoke(state["messages"])]}

graph_builder = StateGraph(State)

# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("bot", bot)


# STEP 3: Add an entry point to the graph
graph_builder.set_entry_point("bot")

# STEP 4: and end point to the graph
graph_builder.set_finish_point("bot")


# STEP 5: Compile the graph
graph = graph_builder.compile()

# res = graph.invoke({"messages": ["Hello, how are you?"]})
# print(res["messages"])

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break
    for event in graph.stream({"messages": ("user", user_input)}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)