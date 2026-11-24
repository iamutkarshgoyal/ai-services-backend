from langgraph.graph import END, StateGraph
from app.graphs.state import AgentState
from app.graphs.router import topic_router, route_topic
from app.tools.Invoice import Invoice_tool
from app.tools.technical import technical_tool
from app.tools.company_policies import company_policies_tool
from langgraph.checkpoint.memory import InMemorySaver


builder = StateGraph(AgentState)
builder.add_node("agent", topic_router)
builder.add_node("invoice_tool", Invoice_tool)
builder.add_node("technical_tool", technical_tool)
builder.add_node("company_policies_tool", company_policies_tool)
builder.set_entry_point("agent")
builder.add_conditional_edges(
    "agent",
    route_topic,
    {
        "invoice_tool": "invoice_tool",
        "technical_tool": "technical_tool",
        "company_policies_tool": "company_policies_tool",
        "end": END,
    },
)
builder.add_edge("invoice_tool", END)
builder.add_edge("technical_tool", END)
builder.add_edge("company_policies_tool", END)

app = builder.compile(checkpointer=InMemorySaver())