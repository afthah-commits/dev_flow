import importlib.util
import os
import sys

# Replace target env file
with open("c:/personal_projects/devflow/backend/alembic/env.py", "r") as f:
    content = f.read()

content = content.replace("target_metadata = None", \"\"\"from app.db.base import Base
target_metadata = Base.metadata\"\"\")

content = content.replace(
    "config.get_main_option(\"sqlalchemy.url\")", 
    "\"\""
)

# Insert config update before context.configure
import_stmt = "from app.core.config import settings\\n"
content = import_stmt + content

patch_str = \"\"\"
def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    from sqlalchemy import create_engine
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()
\"\"\"

import re
content = re.sub(r'def run_migrations_offline.*run_migrations_online\(\)', patch_str, content, flags=re.DOTALL)

with open("c:/personal_projects/devflow/backend/alembic/env.py", "w") as f:
    f.write(content + "\\nif context.is_offline_mode():\\n    run_migrations_offline()\\nelse:\\n    run_migrations_online()\\n")
