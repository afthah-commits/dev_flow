import os
import re

def update_api_client():
    path = "frontend/src/lib/dailyReportApi.ts"
    with open(path, "r") as f:
        content = f.read()

    new_imports = "import { DailyReport, DailyReportCreate, DailyReportUpdate, DailyReportSummaryResponse, TeamDailyReportResponse, BlockerSummaryResponse, WeeklySummaryResponse } from '../types/dailyReport';"
    content = re.sub(r"import \{ .* \} from '../types/dailyReport';", new_imports, content)

    new_methods = """
    getDailySummary: async (date: string, organizationId: string): Promise<DailyReportSummaryResponse> => {
        const response = await fetch(`${API_BASE_URL}/summary/daily?report_date=${date}`, {
            headers: { 'X-Organization-Id': organizationId },
        });
        if (!response.ok) throw new Error('Failed to fetch daily summary');
        return response.json();
    },

    getWeeklySummary: async (startDate: string, organizationId: string): Promise<WeeklySummaryResponse> => {
        const response = await fetch(`${API_BASE_URL}/summary/weekly?start_date=${startDate}`, {
            headers: { 'X-Organization-Id': organizationId },
        });
        if (!response.ok) throw new Error('Failed to fetch weekly summary');
        return response.json();
    },

    getTeamReports: async (date: string, organizationId: string): Promise<TeamDailyReportResponse[]> => {
        const response = await fetch(`${API_BASE_URL}/team?report_date=${date}`, {
            headers: { 'X-Organization-Id': organizationId },
        });
        if (!response.ok) throw new Error('Failed to fetch team reports');
        return response.json();
    },

    getBlockers: async (days: number, organizationId: string): Promise<BlockerSummaryResponse[]> => {
        const response = await fetch(`${API_BASE_URL}/blockers?days=${days}`, {
            headers: { 'X-Organization-Id': organizationId },
        });
        if (!response.ok) throw new Error('Failed to fetch blockers');
        return response.json();
    },
"""
    if "getDailySummary" not in content:
        content = content.replace("export const dailyReportApi = {", "export const dailyReportApi = {" + new_methods)
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    update_api_client()
