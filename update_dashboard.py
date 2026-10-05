import os

def update_dashboard():
    path = "frontend/src/layouts/DashboardLayout.tsx"
    with open(path, "r") as f:
        content = f.read()

    new_dropdown = """
          <div className="relative group">
            <span className="hover:text-white transition-colors cursor-pointer">Daily Reports</span>
            <div className="absolute hidden group-hover:block bg-gray-800 p-2 rounded shadow-lg z-10 w-40">
              <Link to="/daily-reports" className="block text-sm py-1 hover:text-white">My Reports</Link>
              <Link to="/daily-reports/team" className="block text-sm py-1 hover:text-white">Team Reports</Link>
              <Link to="/daily-reports/weekly" className="block text-sm py-1 hover:text-white">Weekly Summary</Link>
              <Link to="/daily-reports/blockers" className="block text-sm py-1 hover:text-white">Blockers</Link>
            </div>
          </div>
"""
    if "Daily Reports" not in content:
        content = content.replace('<Link to="/profile"', new_dropdown.strip() + '\n          <Link to="/profile"')
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    update_dashboard()
