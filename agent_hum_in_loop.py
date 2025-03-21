import os
from typing import Annotated, TypedDict 
from dotenv import load_dotenv

from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import StateGraph, END
from langchain_community.tools.tavily_search import TavilySearchResults


# Load environment variables from .env file
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
tavily = os.getenv("TAVILY_API_KEY")

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


graph_builder = StateGraph(State)

# create tools
tool = TavilySearchResults(max_results=2)
tools = [tool]
# rest = tool.invoke("What is the capital of France?")
# print(rest)

model_with_tools = model.bind_tools(tools)


import json
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition



def bot(state: State):
    # print(state.items())
    print(state["messages"])
    return {"messages": [model_with_tools.invoke(state["messages"])]}




# instantiate the ToolNode with the tools
tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node) # add the node


# The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "__end__" if
# it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "bot",
    tools_condition,
)


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("bot", bot)


# STEP 3: Add an entry point to the graph
graph_builder.set_entry_point("bot")

# Start memory node
from langgraph.checkpoint.sqlite import SqliteSaver
with SqliteSaver.from_conn_string(":memory:") as memory:
    # STEP 5: Compile the graph
    graph = graph_builder.compile(
        checkpointer=memory,
        interrupt_before=["tools"],
    )
    # MEMORY CODE CONTINUES ===
    # Now we can run the chatbot and see how it behaves
    # PICK A TRHEAD FIRST
    config = {
        "configurable": {"thread_id": 1}
    }  # a thread where the agent will dump its memory to
    user_input = "Could you do some research on Tarot and how effective it is"

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {"messages": [("user", user_input)]}, config, stream_mode="values"
    )

    for event in events:
        event["messages"][-1].pretty_print()


    # inspect the state
    snapshot = graph.get_state(config)
    next_step = snapshot.next
    # this will show "action", because we've interrupted the flow before the tools node

    print(
        "===>>>", next_step
    )  # this will show "action", because we've interrupted the flow before the tools node


    existing_message = snapshot.values["messages"][-1]
    all_tools = existing_message.tool_calls

    print("tools to be called::", all_tools)

    # Continue the conversation passing None to say continue - all is good
    # `None` will append nothing new to the current state, letting it resume as if it had never been interrupted
    events = graph.stream(None, config, stream_mode="values")
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()  