# Django Backend (Stage 1)

Production-ready Django 5.x backend for AI project.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env` with your Supabase credentials (DATABASE_URL, OPENAI_API_KEY, etc.)

3. Run migrations:
```bash
python manage.py migrate
```

4. Start dev server:
```bash
python manage.py runserver
```

## Database

Models mapped to existing Supabase tables with `managed = False`:
- **users**: User
- **chats**: Chat, Message, ChatMember, ChatAccess
- **files**: Document, DocumentChunk, ChunkEmbedding

All models registered in Django Admin (`/admin/`).

## Admin panel (quick start)

1. Apply migrations (creates only Django-managed tables such as refresh tokens):
```bash
cd backend
python manage.py migrate
```
2. Create a superuser (for admin access):
```bash
python manage.py createsuperuser --email admin@krok.edu.ua
```
3. Open admin: `https://<YOUR_DOMAIN>/admin/` and sign in.

Notes:
- Existing Supabase tables are mapped with `Meta.managed = False` — Django will not alter them.
- Admin shows `User`, `Chat`, `Message`, `Document`, `DocumentChunk`, `ChunkEmbedding` and the Django-managed `RefreshToken`.
- If you need to add new tables, follow `ADDING_MODELS.md` to ensure migrations are non-destructive.

## Adding Models

See `ADDING_MODELS.md` for detailed instructions on creating new tables and extending existing ones.

## API

- `GET /health/` — health check endpoint

## Deployment

### Docker
```bash
docker build -t django-backend .
docker run -e DATABASE_URL=... -p 8000:8000 django-backend
```

### Render
Push to GitHub. Render will read `render.yaml` and deploy automatically.
