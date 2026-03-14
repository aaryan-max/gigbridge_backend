# PostgreSQL Migration Guide for GigBridge

## Overview
This guide documents the migration from SQLite to PostgreSQL for the GigBridge application.

## Prerequisites

### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Windows
# Download and install from https://www.postgresql.org/download/windows/
```

### 2. Install Python Dependencies
```bash
pip install psycopg2-binary
```

### 3. Create Database and User
```sql
-- Connect to PostgreSQL as superuser
psql postgres

-- Create database
CREATE DATABASE gigbridge;

-- Create user
CREATE USER gigbridge_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE gigbridge TO gigbridge_user;

-- Exit
\q
```

## Environment Variables

Set the following environment variables before running the application:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=gigbridge
export POSTGRES_USER=gigbridge_user
export POSTGRES_PASSWORD=your_secure_password
```

## Migration Steps

### 1. Backup Existing SQLite Data
```bash
# Backup client database
cp client.db client.db.backup

# Backup freelancer database
cp freelancer.db freelancer.db.backup
```

### 2. Run the Application
The application will automatically create the PostgreSQL schema on first run.

```bash
python app.py
```

### 3. Verify Migration
Check that all tables are created in PostgreSQL:

```sql
psql -h localhost -U gigbridge_user -d gigbridge

-- List all tables
\dt

-- Check sample data
SELECT COUNT(*) FROM client;
SELECT COUNT(*) FROM freelancer;
```

## Schema Changes

### Key Differences from SQLite:

1. **Auto-incrementing IDs**: Changed from `INTEGER PRIMARY KEY AUTOINCREMENT` to `SERIAL PRIMARY KEY`
2. **Full-text Search**: Replaced SQLite FTS5 with PostgreSQL GIN index
3. **UPSERT Operations**: Changed `INSERT OR REPLACE` to `ON CONFLICT DO UPDATE`
4. **Ignore Operations**: Changed `INSERT OR IGNORE` to `ON CONFLICT DO NOTHING`

### Full-text Search Implementation

PostgreSQL uses GIN indexes for full-text search:

```sql
-- Created automatically by the application
CREATE INDEX freelancer_search_text_idx 
ON freelancer_search 
USING gin(to_tsvector('english', title || ' ' || skills || ' ' || bio || ' ' || tags || ' ' || portfolio_text));
```

## Configuration Files

### postgres_config.py
New configuration file that handles:
- Database connection management
- Error handling for PostgreSQL-specific exceptions
- Connection pooling (if needed in the future)

### Updated Files
- `database.py`: Updated to use PostgreSQL connections
- `app.py`: Updated all database calls and SQL syntax
- All other files with database connections

## Testing the Migration

### 1. Test Database Connection
```python
from postgres_config import get_postgres_connection

try:
    conn = get_postgres_connection()
    print("✅ PostgreSQL connection successful")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### 2. Test Basic Operations
```python
from database import create_tables

try:
    create_tables()
    print("✅ Tables created successfully")
except Exception as e:
    print(f"❌ Table creation failed: {e}")
```

### 3. Test Application Endpoints
Test key endpoints to ensure functionality:

```bash
# Test client signup
curl -X POST http://localhost:5000/client/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Client","email":"test@example.com","password":"password123"}'

# Test freelancer signup
curl -X POST http://localhost:5000/freelancer/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Freelancer","email":"freelancer@example.com","password":"password123"}'

# Test search functionality
curl "http://localhost:5000/freelancers/all"
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify PostgreSQL is running
   - Check environment variables
   - Ensure database and user exist

2. **Permission Errors**
   - Grant proper privileges to the user
   - Check database ownership

3. **SQL Syntax Errors**
   - PostgreSQL is more strict with data types
   - Check for proper quoting in queries

4. **Performance Issues**
   - Create indexes for frequently queried columns
   - Consider connection pooling for high traffic

### Error Messages and Solutions

**Error**: `FATAL: database "gigbridge" does not exist`
**Solution**: Create the database using `CREATE DATABASE gigbridge;`

**Error**: `FATAL: password authentication failed for user "gigbridge_user"`
**Solution**: Verify password and user exists

**Error**: `psycopg2.OperationalError: could not connect to server`
**Solution**: Check PostgreSQL service is running and connection parameters

## Performance Considerations

### Indexes
The application creates these indexes automatically:
- Primary key indexes on all tables
- GIN index for full-text search
- Unique constraints on email fields

### Connection Pooling
For production, consider implementing connection pooling:
```python
# In postgres_config.py (future enhancement)
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min and max connections
    host=POSTGRES_CONFIG['host'],
    port=POSTGRES_CONFIG['port'],
    database=POSTGRES_CONFIG['database'],
    user=POSTGRES_CONFIG['user'],
    password=POSTGRES_CONFIG['password']
)
```

## Rollback Plan

If you need to rollback to SQLite:

1. Stop the application
2. Restore SQLite databases:
   ```bash
   cp client.db.backup client.db
   cp freelancer.db.backup freelancer.db
   ```
3. Revert code changes (use git)
4. Uninstall psycopg2-binary:
   ```bash
   pip uninstall psycopg2-binary
   ```

## Production Deployment

### Security Considerations
- Use strong passwords
- Enable SSL connections
- Restrict network access to PostgreSQL
- Regular backups

### Environment Setup
```bash
# Production environment variables
export POSTGRES_HOST=your-db-host
export POSTGRES_PORT=5432
export POSTGRES_DB=gigbridge_prod
export POSTGRES_USER=gigbridge_app
export POSTGRES_PASSWORD=strong_production_password
```

### Backup Strategy
```bash
# Regular PostgreSQL backups
pg_dump -h localhost -U gigbridge_user gigbridge > backup_$(date +%Y%m%d).sql

# Automated backup script (optional)
# Add to crontab for daily backups
0 2 * * * pg_dump -h localhost -U gigbridge_user gigbridge > /backups/gigbridge_$(date +\%Y\%m\%d).sql
```

## Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database and user created
- [ ] Environment variables set
- [ ] Application starts without errors
- [ ] Tables created successfully
- [ ] Basic CRUD operations work
- [ ] Search functionality works
- [ ] Authentication works
- [ ] File uploads work
- [ ] All API endpoints respond correctly

## Support

For issues with the migration:
1. Check PostgreSQL logs
2. Review application logs
3. Verify environment configuration
4. Test with simple database operations first
