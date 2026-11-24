from app.graphs.state import CompanyPolicyState
from app.tools.Invoice import _require
from langgraph.types import interrupt
from app.repositories.company_policy_repository import update_paid_leave_0, update_paid_leave_sick_leave_0, update_sick_leave_data, leave_balance
from app.graphs.approvals import Leave_balance_approval

Company_Policies_database = [
    {
        "policy_id": "Policy1",
        "title": "Leave Policy",
        "content": "This is the content of the Leave Policy."
    },
    {
        "policy_id": "Policy2",
        "title": "Code of Conduct",
        "content": "This is the content of the Code of Conduct."
    },
    {
        "policy_id": "Policy3",
        "title": "Remote Work Policy",
        "content": "This is the content of the Remote Work Policy."
    }
]


def company_policies_tool(state: CompanyPolicyState) -> dict:
    _require(state.intent, "intent")

    approved_updates = []
    rejected_updates = []

    if "get_policy_details" in state.intent:
        _require(state.policy_id, "policy_id")
        for entry in Company_Policies_database:
            if entry["policy_id"] == state.policy_id:
                return {
                    "response": f"Policy Details for {state.policy_id}: Title: {entry['title']}, Content: {entry['content']}"
                }

    elif any(intent in {"update_sick_leave", "update_paid_leave"} for intent in state.intent):
        _require(state.employee_id, "employee_id")
   
        if "update_sick_leave" in state.intent:
            _require(state.sick_leave, "sick_leave")

            leave_data = leave_balance()
            Total_paid_leave_balance, Total_sick_leave_balance = leave_data.get("paid_leave"), leave_data.get("sick_leave")

            if Total_sick_leave_balance >= state.sick_leave:
                result = update_sick_leave_data()
                if result.rowcount != 1:
                        raise RuntimeError(f"Unable to update leave balance.")
            else:
                decision = interrupt(
                    {
                        "question": (f"The requested sick leave {state.sick_leave} exceeds the current balance of {Total_sick_leave_balance}. "
                                        f"Do you want to proceed with deducting the remaining days from paid leave? "
                                        f"You have {Total_paid_leave_balance} paid leave balance. Do you want to proceed?"),
                        "type": "Sick leave approval",
                        "allowed_responses": ["yes", "no"],
                        "approved": [True, False],
                    }
                )

                approval = Leave_balance_approval.model_validate(decision)

                if approval.approved:
                    approved_updates.append(("sick_leave", state.sick_leave))  
                    result = update_paid_leave_sick_leave_0(sick_leave_balance=Total_sick_leave_balance)

                    if result.rowcount != 1:
                        raise RuntimeError(f"Unable to update leave balance.")
                        
                else:
                    rejected_updates.append(("sick_leave", state.sick_leave))
                        
        elif "update_paid_leave" in state.intent:
            _require(state.paid_leave, "paid_leave")

            leave_data = leave_balance()
            Total_paid_leave_balance, employee_name = leave_data.get("paid_leave"), leave_data.get("employee_name")

            decision = interrupt(
                {
                    "question": (f"Employee {employee_name} (ID: {state.employee_id}) has current paid leave balance of "
                    f"{Total_paid_leave_balance}. Do you still want to update it to {state.paid_leave}?"),
                    "type": "approval",
                    "allowed_responses": ["yes", "no"],
                }
            )
            approval = Leave_balance_approval.model_validate(decision)

            if approval.approved:
                approved_updates.append(("paid_leave", state.paid_leave))
                result = update_paid_leave_0()

                if result.rowcount != 1:
                    raise RuntimeError(f"Unable to update leave balance.")

            else:
                rejected_updates.append(("paid_leave", state.paid_leave))

    leave_data = leave_balance()
    Total_paid_leave_balance, Total_sick_leave_balance = leave_data.get("paid_leave"), leave_data.get("sick_leave")

    return {
        "response": (
            f"Company policy processing completed. "
            f"Remaining sick leave balance: {Total_sick_leave_balance}, Remaining paid leave balance: {Total_paid_leave_balance}. "
            f"Approved updates: {', '.join(f'{col} = {val}' for col, val in approved_updates) or 'None'}. "
            f"Rejected updates: {', '.join(f'{col} = {val}' for col, val in rejected_updates) or 'None'}."
        )
    }