from langchain_ollama import ChatOllama
from pydantic import BaseModel
from typing import Literal
from app.graphs.state import InvoiceState, TechnicalState, CompanyPolicyState
from app.graphs.state import AgentState


LLM = ChatOllama(
    model="qwen3:4b",
    temperature=0,
    reasoning=False,
    num_ctx=4096,
    num_predict=256,
    keep_alive="30m",
)


class RouteDecision(BaseModel):
    topic: Literal["Invoice", "Technical", "Company Policies", "Other"]


ROUTER = LLM.with_structured_output(RouteDecision)
INVOICE_EXTRACTOR = LLM.with_structured_output(InvoiceState)
TECHNICAL_EXTRACTOR = LLM.with_structured_output(TechnicalState)
COMPANY_POLICY_EXTRACTOR = LLM.with_structured_output(CompanyPolicyState)


def topic_router(state: AgentState) -> dict:
    """
    This function takes the AgentState as input and returns a dictionary containing the topic and extracted information based on the topic.
    Args: state (AgentState): The current state of the agent, including the conversation ID and message
    Returns: dict: A dictionary containing the topic and extracted information based on the topic.
    """

    route = ROUTER.invoke(
        "Classify this request into exactly one topic: Invoice, Technical, "
        f"Company Policies, or Other. Request: {state.message!r}")

    update: dict = {"topic": route.topic}
    if route.topic == "Invoice":
        request = INVOICE_EXTRACTOR.invoke(
            """Extract the invoice intent and only values explicitly stated by the user. 
            if any date is provided which can be in any format like YYYY-MM-DD identify it and return the date into string format keep the date inside "" like "2024-07-15".,
            Use null for every value that is not stated. """
            f"Request: {state.message!r}")

        print(request)
        
        update.update(request.model_dump())
        if any(intent in {"get_invoice_details", "get_invoice_pdf"} for intent in request.intent):
            update.update(
                invoice_date=None,
                due_date=None,
                total_amount=None,
                status=None,)
            
        elif request.intent == "other":
            state.response = LLM.invoke(
                """Understand the question and ask Invoice Number if not already provided and as we can provide assistance on invoice update, 
                invoice pdf extraction and invoice related queries. """
                f"Request: {state.message!r}")
            print(state.response)
            
            
    elif route.topic == "Technical":
        request = TECHNICAL_EXTRACTOR.invoke(
            "Extract the technical request details and only values explicitly stated by the user. "
            "Use null for every value that is not stated. "
            f"Request: {state.message!r}")
        update.update(request.model_dump())

    elif route.topic == "Company Policies":
        request = COMPANY_POLICY_EXTRACTOR.invoke(
            "Extract the intent and company policy request details and only values explicitly stated by the user. "
            "If user is asking to apply means they want to update the leave balance. "
            "also if user want to update sick leave then intent would be update_sick_leave and if user want to update paid leave then intent would be update_paid_leave. "
            "Use null for every value that is not stated. "
            f"Request: {state.message!r}")
        update.update(request.model_dump())

        if "get_policy_details" in request.intent:
            update.update(
                employee_id=None,
                employee_name=None,
                sick_leave=None,
                paid_leave=None,)

        elif "update_sick_leave" in request.intent:
            update.update(
                title=None,
                employee_name=None,
                paid_leave=None,)

        elif "update_paid_leave" in request.intent:
            update.update(
                title=None,
                employee_name=None,
                sick_leave=None,)

    elif route.topic == "Other":
        response = LLM.invoke(
            "You are an AI assistant that can only answer questions to user only in 2-3 lines."
            f"Request: {state.message!r}")
        update.update({"response": response.content})
    return update


def route_topic(state: RouteDecision) -> str:
    return {
        "Invoice": "invoice_tool",
        "Technical": "technical_tool",
        "Company Policies": "company_policies_tool",
        "Other": "end",
    }.get(state.topic, "end")
