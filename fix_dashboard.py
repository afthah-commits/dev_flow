with open('backend/app/api/v1/dashboard.py', 'r') as f:
    c = f.read()

optimized_sprints = '''    sprints = db.query(Sprint).join(Project).filter(
        Project.organization_id == org_id,
        Sprint.status == SprintStatus.ACTIVE
    ).all()
    
    sprint_ids = [s.id for s in sprints]
    
    if not sprint_ids:
        return []
        
    from sqlalchemy import func
    from app.models.task import Task
    
    # Batch query stats
    stats = db.query(
        Task.sprint_id,
        func.sum(Task.estimate_points).label('total_pts'),
        func.sum(
            func.case(
                (Task.status == TaskStatus.DONE, Task.estimate_points),
                else_=0
            )
        ).label('completed_pts')
    ).filter(
        Task.sprint_id.in_(sprint_ids)
    ).group_by(Task.sprint_id).all()
    
    stats_map = {row.sprint_id: {"total": row.total_pts or 0.0, "completed": row.completed_pts or 0.0} for row in stats}
    
    result = []
    for s in sprints:
        sprint_stats = stats_map.get(s.id, {"total": 0.0, "completed": 0.0})
        result.append({
            "id": s.id,
            "name": s.name,
            "project_id": s.project_id,
            "total_points": sprint_stats["total"],
            "completed_points": sprint_stats["completed"]
        })
'''

import re
# Use regex to replace the old loop
c = re.sub(r'    sprints = db.query\(Sprint\).*?            \}\)\n', optimized_sprints, c, flags=re.DOTALL)

with open('backend/app/api/v1/dashboard.py', 'w') as f:
    f.write(c)
