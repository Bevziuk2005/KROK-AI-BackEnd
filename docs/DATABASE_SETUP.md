# Database Initialization Guide

This guide explains how to set up Django with existing Supabase PostgreSQL tables.

## Prerequisites

- Supabase PostgreSQL database with existing tables
- Django 5.x installed
- `.env` file configured with `DATABASE_URL`

## Architecture Overview

### Managed vs Unmanaged Models

This project uses a **hybrid approach** for database management:

1. **Unmanaged Models** (`managed = False`): Represent existing Supabase tables
   - Django does NOT create or modify these tables
   - Migrations describe their structure but don't execute
   - Examples: `User`, `Chat`, `Message`, `Document`, `DocumentChunk`, `ChunkEmbedding`

2. **Managed Models** (`managed = True`, default): Django-created and managed
   - Django creates, modifies, and deletes these tables
   - Standard Django migration workflow applies
   - Examples: `RefreshToken`, `User` (only auth fields)

## Step-by-Step Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create or update `.env`:
```bash
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SECRET_KEY=your-secret-key-here
DEBUG=False
```

### 3. Initialize Database
Run the custom initialization command:
```bash
python manage.py init_db
```

This command:
- Runs all migrations with `--fake-initial` flag
- Marks initial migrations as applied WITHOUT executing them
- Creates only Django-managed tables (e.g., RefreshToken)
- Verifies database connectivity

### 4. Verify Installation
```bash
python manage.py check
python manage.py showmigrations
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser --email admin@example.com
```

## Migration Structure

### Migration Files

Each app contains migrations for its models:

- **apps/users/migrations/**
  - `0001_create_refreshtoken.py` - Django-managed RefreshToken model
  - `0002_user.py` - Existing User table (managed=False, fake-initial)

- **apps/chats/migrations/**
  - `0001_initial.py` - Existing Chat, Message, ChatMember, ChatAccess (managed=False, fake-initial)

- **apps/files/migrations/**
  - `0001_add_error_message.py` - Document.error_message field (managed=True)
  - `0002_initial.py` - Existing Document, DocumentChunk, ChunkEmbedding (managed=False, fake-initial)

### How Fake-Initial Works

When Django encounters a `0001_initial` migration with `managed = False`:

1. **Without `--fake-initial`** (error):
   ```
   Error: CREATE TABLE failed - table already exists
   ```

2. **With `--fake-initial`** (success):
   - Django reads the migration definition
   - Marks migration as applied in `django_migrations` table
   - Does NOT execute CREATE TABLE
   - Models become available for use

## Adding New Models

If you need to add new Django-managed tables:

1. Create the model in the appropriate `models.py`
2. Ensure `managed = True` (default)
3. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

For new Supabase tables:
1. Create the table in Supabase manually
2. Create a new model with `managed = False`
3. Create an initial migration describing the table
4. Run `python manage.py migrate --fake-initial`

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
python manage.py dbshell

# Check migrations
python manage.py showmigrations

# Verbose output
python manage.py migrate --verbosity=3
```

### Migration Issues

**Problem**: "Relation does not exist"
```bash
# Solution: Run initialization command
python manage.py init_db
```

**Problem**: "Table already exists"
```bash
# This usually means --fake-initial wasn't used. Safe to ignore for managed=False tables.
# The command `init_db` handles this correctly.
```

**Problem**: Migrations are out of sync
```bash
# Check status
python manage.py showmigrations

# Force mark as applied (use with caution)
python manage.py migrate --fake app_name 0001_initial
```

## Environment-Specific Configuration

### Development (SQLite)
```bash
# No DATABASE_URL needed; uses local db.sqlite3
DEBUG=True
```

### Staging/Production (Supabase)
```bash
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
DEBUG=False
```

## Verification Checklist

- [ ] `.env` configured with `DATABASE_URL`
- [ ] Database connection successful: `python manage.py dbshell`
- [ ] Migrations initialized: `python manage.py showmigrations` shows all as `[X]`
- [ ] Models accessible: `python manage.py shell` → `from apps.users.models import User; User.objects.count()`
- [ ] Admin working: `python manage.py createsuperuser` then `/admin/`

## Advanced: Manual Migration Steps

If you prefer not to use `init_db`:

```bash
# Step 1: Check current state
python manage.py showmigrations

# Step 2: Mark initial migrations as applied (fake them)
python manage.py migrate --fake-initial

# Step 3: Apply any pending migrations
python manage.py migrate

# Step 4: Verify
python manage.py check
python manage.py showmigrations
```

## Resources

- [Django Documentation: Migrations](https://docs.djangoproject.com/en/5.0/topics/migrations/)
- [Django Documentation: Meta Options](https://docs.djangoproject.com/en/5.0/ref/models/options/#managed)
- [Supabase PostgreSQL](https://supabase.com/docs/guides/database)
