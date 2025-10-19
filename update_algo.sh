# 1) drop the old templates (wrap in a transaction for safety)
docker exec -i trading_postgres_dev psql \
  -U trading_user -d trading_dev <<'SQL'
BEGIN;
DELETE FROM algorithm_templates;
COMMIT;
SQL

# 2) replay the updated seed script
cat database/migrations/20-seed-algorithm-templates.sql | \
  docker exec -i trading_postgres_dev psql \
    -U trading_user -d trading_dev


