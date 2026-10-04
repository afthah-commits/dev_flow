import re

with open(r"src/pages/AdminSystem.tsx", "r", encoding="utf-8") as f:
    content = f.read()

jobs_dashboard = """
      <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg md:col-span-3 mt-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <Activity className="text-blue-400 w-5 h-5" /> Job Operations
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><div className="text-gray-500">Queue Depth</div><div className="text-xl text-white">{jobStats?.queue_depth || 0}</div></div>
            <div><div className="text-gray-500">24h Throughput</div><div className="text-xl text-white">{jobStats?.throughput_24h || 0}</div></div>
            <div><div className="text-gray-500">Success Rate</div><div className="text-xl text-green-400">{jobStats?.success_rate_24h || 0}%</div></div>
            <div><div className="text-gray-500">Failure Rate</div><div className="text-xl text-red-400">{jobStats?.failure_rate_24h || 0}%</div></div>
            <div><div className="text-gray-500">Avg Execution Time</div><div className="text-xl text-white">{jobStats?.avg_execution_time_sec || 0}s</div></div>
            <div><div className="text-gray-500">Active (Running)</div><div className="text-xl text-blue-400">{jobStats?.RUNNING || 0}</div></div>
            <div><div className="text-gray-500">Retrying</div><div className="text-xl text-yellow-400">{jobStats?.RETRYING || 0}</div></div>
        </div>
      </div>
"""

if "jobStats" not in content:
    content = content.replace("const [stats, setStats] = useState<any>(null);", "const [stats, setStats] = useState<any>(null);\n  const [jobStats, setJobStats] = useState<any>(null);")
    content = content.replace("api.get('/admin/system')", "api.get('/jobs/stats').then(res => setJobStats(res.data)).catch(err => console.error(err));\n    api.get('/admin/system')")
    content = content[:content.rfind("</div>")] + jobs_dashboard + "</div>"

with open(r"src/pages/AdminSystem.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
