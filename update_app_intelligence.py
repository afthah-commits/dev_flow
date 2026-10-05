import os

def update_app_routes():
    path = "frontend/src/App.tsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    imports = """
import TeamDailyReports from './pages/TeamDailyReports';
import WeeklyDailyReports from './pages/WeeklyDailyReports';
import BlockerDailyReports from './pages/BlockerDailyReports';
"""
    if "TeamDailyReports" not in content:
        content = content.replace("import DailyReportDetails from './pages/DailyReportDetails';", "import DailyReportDetails from './pages/DailyReportDetails';" + imports)
        
        routes = """
                                <Route path="daily-reports/team" element={<TeamDailyReports />} />
                                <Route path="daily-reports/weekly" element={<WeeklyDailyReports />} />
                                <Route path="daily-reports/blockers" element={<BlockerDailyReports />} />
"""
        content = content.replace('<Route path="daily-reports" element={<DailyReports />} />', '<Route path="daily-reports" element={<DailyReports />} />' + routes)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    update_app_routes()
