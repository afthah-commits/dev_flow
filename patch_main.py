import os

def update_main():
    path = "backend/app/main.py"
    with open(path, "r") as f:
        content = f.read()

    # Import
    if "daily_reports" not in content:
        content = content.replace(
            "from app.api.v1 import auth, projects,",
            "from app.api.v1 import daily_reports, auth, projects,"
        )
        
        # Include router
        if "app.include_router(daily_reports.router" not in content:
            router_str = 'app.include_router(daily_reports.router, prefix=f"{settings.API_V1_STR}/daily-reports", tags=["daily-reports"])\n'
            # Insert after auth router
            content = content.replace(
                'app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])',
                'app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])\n' + router_str
            )
            
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    update_main()
