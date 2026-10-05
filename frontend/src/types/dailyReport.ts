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
