# Database Backup and Recovery

DevFlow's state is fully contained in the PostgreSQL database.

## Backup Strategy
Use standard PostgreSQL tools like `pg_dump` to create logical backups:

```bash
pg_dump -U devflow -d devflow -F c -f devflow_backup_$(date +%Y%m%d).dump
```

For production deployments on cloud providers (e.g., AWS RDS, GCP Cloud SQL), it's highly recommended to use automated snapshot backups.

## Restore Strategy
To restore a backup into a fresh database:

```bash
# Drop/recreate database if necessary (Caution!)
pg_restore -U devflow -d devflow -1 devflow_backup_XXXXXX.dump
```

## Migrations Rollback
If a deployment fails, you can rollback database migrations using Alembic:

```bash
# Downgrade 1 revision
docker-compose exec backend alembic downgrade -1

# Downgrade to specific revision
docker-compose exec backend alembic downgrade <revision_id>
```
