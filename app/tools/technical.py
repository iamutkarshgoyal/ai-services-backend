from app.graphs.state import TechnicalState
from app.tools.Invoice import _require
from langgraph.types import interrupt

Technical_database = [
    {
        "project": "ProjectX",
        "language": "Python",
        "code_snippet": "this is a sample Python code snippet for ProjectX."
    },
    {
        "project": "ProjectY",
        "language": "JavaScript",
        "code_snippet": "this is a sample JavaScript code snippet for ProjectY."
    },
    {
        "project": "ProjectZ",
        "language": "Java",
        "code_snippet": "this is a sample Java code snippet for ProjectZ."
    },
    {
        "project": "ProjectA",
        "language": "C++",
        "code_snippet": "this is a sample C++ code snippet for ProjectA."
    }
]


def technical_tool(state: TechnicalState) -> dict:
    _require(state.project, "project")
    _require(state.language, "language")

    if "language_update" in state.intent:
        for entry in Technical_database:
            if entry["project"] == state.project:
                if entry["language"] != state.language:
                    decision = interrupt(
                        {
                            "question": (
                                f"Update language for project {state.project} "
                                f"from {entry['language']} to {state.language}?"
                            ),
                            "type": "approval",
                            "allowed_responses": ["yes", "no"],
                        },
                    )
                    if not decision.get("approved", False):
                        return {
                            "response": f"Language update for project {state.project} cancelled."
                        }
                    entry["language"] = state.language
                    return {
                        "response": f"Language for project {state.project} updated to {state.language}."
                    }
                else:
                    return {
                        "response": f"Project {state.project} already has language {state.language}."
                    }   

    elif any(intent in {"code_review", "bug_fix", "feature_request"} for intent in state.intent):
        for entry in Technical_database:
            if entry["project"] == state.project and entry["language"] == state.language:
                if state.code_snippet:
                    decision = interrupt(
                        {
                            "question": (f"Process {state.intent} for project {state.project} with the provided code snippet?"),
                            "type": "approval",
                            "allowed_responses": ["yes", "no"],
                        }
                    )
                    if not decision.get("approved", False):
                        return {
                            "response": f"{state.intent} for project {state.project} cancelled."
                        }
                    return {
                        "response": f"Processed {state.intent} for project {state.project} with provided code snippet."
                    }
                else:
                    return {
                        "response": f"No code snippet provided for {state.intent} in project {state.project}."
                    }
    return {"response": "Route this request to your technical knowledge/tool node."}