import os

def update_app_tsx():
    path = "frontend/src/App.tsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Import components
    if "DailyReports" not in content:
        imports = """
import DailyReports from './pages/DailyReports';
import DailyReportForm from './pages/DailyReportForm';
import DailyReportDetails from './pages/DailyReportDetails';
"""
        content = content.replace("import AdminSystem from './pages/AdminSystem';", "import AdminSystem from './pages/AdminSystem';" + imports)
        
        # Add routes
        routes = """
                                <Route path="daily-reports" element={<DailyReports />} />
                                <Route path="daily-reports/new" element={<DailyReportForm />} />
                                <Route path="daily-reports/:id" element={<DailyReportDetails />} />
                                <Route path="daily-reports/:id/edit" element={<DailyReportForm />} />
"""
        # find where to insert: inside DashboardLayout
        content = content.replace('<Route path="reports" element={<Reports />} />', '<Route path="reports" element={<Reports />} />' + routes)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    update_app_tsx()
