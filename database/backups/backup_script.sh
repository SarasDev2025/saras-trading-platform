# Complete database backup (schema + data)
docker exec trading_postgres_dev pg_dump -U trading_user -d trading_dev > backup_full_$(date +%Y%m%d_%H%M%S).sql

# Schema-only backup (structure without data)
docker exec trading_postgres_dev pg_dump -U trading_user -d trading_dev --schema-only > backup_schema_$(date +%Y%m%d_%H%M%S).sql

# Data-only backup (data without structure)
docker exec trading_postgres_dev pg_dump -U trading_user -d trading_dev --data-only > backup_data_$(date +%Y%m%d_%H%M%S).sql