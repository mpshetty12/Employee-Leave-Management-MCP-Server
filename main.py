from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
from datetime import datetime, timedelta

mcp = FastMCP("EmployeeLeaveManagement")

# Pre-populate some employees with balances and empty history
employees = {}

def daterange(start_date: datetime, end_date: datetime):
    """Generator for dates from start_date to end_date inclusive."""
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)

def dates_overlap(existing_dates: List[datetime], new_dates: List[datetime]) -> bool:
    existing_set = set(existing_dates)
    new_set = set(new_dates)
    return not existing_set.isdisjoint(new_set)

@mcp.tool()
def apply_leave(employee: str, leave_type: str, start: str, end: str, reason: str = "") -> str:
    """
    Apply leave for an employee over a date range.
    Dates format: YYYY-MM-DD (ISO)
    """

    emp = employees.get(employee)
    if not emp:
        return f"Employee '{employee}' not found."

    if leave_type not in emp["balances"]:
        return f"Invalid leave type '{leave_type}'. Valid types: {list(emp['balances'].keys())}"

    # Parse dates
    try:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD."

    if end_date < start_date:
        return "End date cannot be before start date."

    # Calculate number of days requested
    num_days = (end_date - start_date).days + 1

    if num_days > emp["balances"][leave_type]:
        return f"Insufficient {leave_type} leave balance. Available: {emp['balances'][leave_type]} days."

    # Collect all dates of leave requested
    requested_dates = list(daterange(start_date, end_date))

    # Collect all previously taken leave dates regardless of type
    taken_dates = []
    for record in emp["history"]:
        rec_start = datetime.fromisoformat(record["start"])
        rec_end = datetime.fromisoformat(record["end"])
        taken_dates.extend(daterange(rec_start, rec_end))

    # Check for overlapping leave dates
    if dates_overlap(taken_dates, requested_dates):
        return "Leave dates overlap with previously approved leave. You cannot take multiple leaves on the same day."

    # Deduct leave balance
    emp["balances"][leave_type] -= num_days

    # Add to history
    leave_record = {
        "type": leave_type,
        "start": start,
        "end": end,
        "days": num_days,
        "reason": reason,
        "applied_at": datetime.now().isoformat()
    }
    emp["history"].append(leave_record)

    return f"Leave approved for {num_days} day(s) ({start} to {end}) of {leave_type} leave for {employee}."

@mcp.tool()
def get_leave_balance(employee: str) -> Dict[str, int]:
    emp = employees.get(employee)
    if not emp:
        return {"error": f"Employee '{employee}' not found."}
    return emp["balances"]

@mcp.tool()
def get_leave_history(employee: str) -> List[Dict[str, Any]]:
    emp = employees.get(employee)
    if not emp:
        return {"error": f"Employee '{employee}' not found."}
    return emp["history"]

@mcp.tool()
def register_employee(name: str) -> str:
    if name in employees:
        return f"Employee '{name}' is already registered."
    employees[name] = {
        "balances": {"casual": 8, "floater": 2, "sick": 30},
        "history": []
    }
    return f"Employee '{name}' registered with default leave balances."


def main():
    print("Hello I'm Employee Leave Management MCP Server!")


if __name__ == "__main__":
    main()
