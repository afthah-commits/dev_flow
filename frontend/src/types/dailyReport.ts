export interface DailyReport {
    id: string;
    organization_id: string;
    author_user_id: string;
    report_date: string;
    completed_tasks: string[];
    next_plan: string[];
    blockers: string[];
    created_at: string;
    updated_at: string | null;
}

export interface DailyReportCreate {
    report_date: string;
    completed_tasks: string[];
    next_plan: string[];
    blockers: string[];
}

export interface DailyReportUpdate {
    report_date?: string;
    completed_tasks?: string[];
    next_plan?: string[];
    blockers?: string[];
}

export interface DailyReportSummaryResponse {
    total_reports: number;
    completed_task_count: number;
    next_plan_count: number;
    blocker_count: number;
    unique_contributors: number;
    missing_reports: number;
    date?: string;
}

export interface TeamDailyReportResponse extends DailyReport {
    author_name?: string;
}

export interface BlockerSummaryResponse {
    blocker: string;
    occurrences: number;
    latest_report_date: string;
    reporters: string[];
}

export interface DailyTrendItem {
    date: string;
    reports_submitted: number;
    completed_tasks: number;
}

export interface WeeklySummaryResponse {
    start_date: string;
    end_date: string;
    total_reports: number;
    completed_tasks: number;
    blockers: number;
    trend: DailyTrendItem[];
}
