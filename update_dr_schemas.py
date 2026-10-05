import os

def update_schemas():
    path = "backend/app/schemas/daily_report.py"
    with open(path, "r") as f:
        content = f.read()
    
    new_schemas = """
class DailyReportSummaryResponse(BaseModel):
    total_reports: int
    completed_task_count: int
    next_plan_count: int
    blocker_count: int
    unique_contributors: int
    missing_reports: int
    date: Optional[date] = None

class TeamDailyReportResponse(DailyReportResponse):
    author_name: Optional[str] = None

class BlockerSummaryResponse(BaseModel):
    blocker: str
    occurrences: int
    latest_report_date: date
    reporters: List[str]

class DailyTrendItem(BaseModel):
    date: date
    reports_submitted: int
    completed_tasks: int

class WeeklySummaryResponse(BaseModel):
    start_date: date
    end_date: date
    total_reports: int
    completed_tasks: int
    blockers: int
    trend: List[DailyTrendItem]
"""
    if "DailyReportSummaryResponse" not in content:
        with open(path, "a") as f:
            f.write(new_schemas)

if __name__ == "__main__":
    update_schemas()
