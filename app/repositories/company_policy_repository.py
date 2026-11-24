from app.database.connection import engine
from sqlalchemy import text
from app.graphs.state import CompanyPolicyState

conn = engine.begin()


def leave_balance(state: CompanyPolicyState) -> dict:
    sick_leave, paid_leave, employee_name = (
    conn.execute(
        text(
            """
            SELECT sick_leave, paid_leave, employee_name 
            FROM public.ATTENDANCE WHERE employee_id = :employee_id
            """),
            {"employee_id": state.employee_id},).first())
    return {"sick_leave": sick_leave, "paid_leave": paid_leave, "employee_name": employee_name}


def update_sick_leave_data(state: CompanyPolicyState):
    result = conn.execute(
        text(
            """
            UPDATE public.ATTENDANCE
            SET sick_leave = sick_leave - :sick_leave
            WHERE employee_id = :employee_id
            """),
            {"sick_leave": state.sick_leave, "employee_id": state.employee_id})
    
    return result


def update_paid_leave_sick_leave_0(state: CompanyPolicyState, sick_leave_balance: str):
    result = conn.execute(
        text(
            """UPDATE public.ATTENDANCE
            SET sick_leave = 0, paid_leave = paid_leave - :remaining_days
            WHERE employee_id = :employee_id
            """),
            {"remaining_days": state.sick_leave - sick_leave_balance, "employee_id": state.employee_id}) 

    return result


def update_paid_leave_0(state: CompanyPolicyState):
    result = conn.execute(
        text("""
            UPDATE public.ATTENDANCE
            SET paid_leave = paid_leave - :paid_leave
            WHERE employee_id = :employee_id
            """),
            {"paid_leave": state.paid_leave, "employee_id": state.employee_id})