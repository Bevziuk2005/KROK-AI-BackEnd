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

## API Documentation (для frontend розробника)

Нижче — перелік уже реалізованих endpoint'ів, приклади запитів і необхідні заголовки.

Загальні примітки:
- Усі захищені ендпоінти використовують JWT у заголовку `Authorization: Bearer <access_token>`.
- Refresh токени зберігаються серверно у таблиці `django_refresh_tokens` і передаються як plain string клієнту.
- OpenAI та Supabase повинні бути налаштовані через змінні середовища: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- Microsoft OAuth налаштований через `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT_ID`, `MS_REDIRECT_URI`.
- Токени підписуються HMAC-SHA256 із `SECRET_KEY` з `project.settings`.

1) Authentication (Microsoft Entra ID)

- POST /api/v1/auth/login/
	- Повертає `auth_url` — URL куди фронтенд має перенаправити користувача для авторизації в Microsoft.
	- Тіло (JSON): `{ "redirect": "https://frontend/callback" }` (optional)

- POST /api/v1/auth/callback/
	- Обмінює `code` на `id_token`, валідуює email домен та повертає JWT токени.
	- Тіло (JSON): `{ "code": "<code>", "redirect": "https://frontend/callback" }`
	- Відповідь: `{ "access_token": "<jwt>", "refresh_token": "<refresh>" }`

- POST /api/v1/auth/refresh/
	- Оновити access token
	- Тіло: `{ "refresh_token": "<refresh>" }`
	- Відповідь: `{ "access_token": "<jwt>" }`

- POST /api/v1/auth/logout/
	- Ревокує refresh token
	- Тіло: `{ "refresh_token": "<refresh>" }`

Приклад (curl):

```bash
curl -X POST https://api.example.com/api/v1/auth/refresh/ \
	-H "Content-Type: application/json" \
	-d '{"refresh_token":"<refresh>"}'
```

2) Users

- GET /api/v1/users/me/ — Повертає інформацію про поточного користувача.
- PATCH /api/v1/users/me/ — Часткове оновлення (наприклад `{"email_verified": true}`).
- DELETE /api/v1/users/me/ — Видалити власний обліковий запис.

Приклад заголовка авторизації:

```text
Authorization: Bearer <access_token>
```

3) Chats & Messages

- GET /api/v1/chats/ — Список чатів, доступних користувачу (власні, членство, доступи).
	- Підтримує фільтрацію `?type=assistant` та пошук `?search=term`.
	- Підтримує пагінацію `?page=1&page_size=20`.

- POST /api/v1/chats/ — Створити чат
	- Тіло: `{ "title": "Назва", "type": "assistant" }`

- GET /api/v1/chats/{chat_id}/ — Отримати чат
- PATCH /api/v1/chats/{chat_id}/ — Оновити (лише власник може оновлювати)
- DELETE /api/v1/chats/{chat_id}/ — Soft-delete (лише власник)

- GET /api/v1/chats/{chat_id}/messages/ — Список повідомлень чату (пагінація)
- POST /api/v1/chats/{chat_id}/messages/ — Додати повідомлення
	- Тіло: `{ "role": "user", "content": "Текст", "token_count": 10 }`

- GET /api/v1/messages/{message_id}/ — Отримати повідомлення

Приклад створення повідомлення:

```bash
curl -X POST https://api.example.com/api/v1/chats/<chat_id>/messages/ \
	-H "Authorization: Bearer <access_token>" \
	-H "Content-Type: application/json" \
	-d '{"role":"user","content":"Привіт","token_count":5}'
```

4) Files & RAG

- POST /api/v1/files/upload/ — Завантаження файлу (multipart/form-data)
	- Поля: `file` (обов'язково), `title` (опціонально)
	- Підтримувані MIME за замовчуванням: `text/plain`, `text/markdown` (перевірка сервера)
	- Обмеження розміру за замовчуванням: 10 MB (налаштовується через `MAX_FILE_UPLOAD_SIZE`).

- GET /api/v1/files/ — Список документів власника (пагінація)
- GET /api/v1/files/{file_id}/ — Метадані документа
- DELETE /api/v1/files/{file_id}/ — Видалення документа

- POST /api/v1/files/{file_id}/process/ — Запустити обробку документа у фоні
	- Фоновий процес: розбиття на чанки + генерація ембедінгів (OpenAI) + збереження у базу
	- Повертає 202 Accepted, обробка виконується у фоні (поточна реалізація використовує thread; для production рекомендується Celery/RQ)

- GET /api/v1/files/{file_id}/chunks/ — Повертає чанки документа (пагінація)

- POST /api/v1/rag/search/ — Семантичний пошук по ембедінгам
	- Тіло: `{ "query": "питання...", "top_k": 5 }`
	- Відповідь: список найбільш схожих чанків з полем `similarity`.

Приклад завантаження файлу (curl):

```bash
curl -X POST https://api.example.com/api/v1/files/upload/ \
	-H "Authorization: Bearer <access_token>" \
	-F "file=@./document.txt" \
	-F "title=Документ 1"
```

Приклад виклику RAG search:

```bash
curl -X POST https://api.example.com/api/v1/rag/search/ \
	-H "Authorization: Bearer <access_token>" \
	-H "Content-Type: application/json" \
	-d '{"query":"Як подати заявку?","top_k":3}'
```

5) Тестування

- Локально запустити тести:

```bash
python -m pytest -q
```

6) Корисні підказки для фронтенду
- Зберігайте `refresh_token` у безпечному httpOnly cookie або secure storage; refresh токен потрібен для отримання нового access token.
- Redirect URI у Microsoft має збігатися з `MS_REDIRECT_URI` у середовищі.
- Для потоків, де потрібна синхронна доступність (після upload — process), фронтенд повинен опитувати `/files/{id}/` або `/files/{id}/chunks/` доки статус документа не стане `completed`.

Якщо потрібно — можу додати Postman/HTTP-колекцію з готовими запитами та примерами відповіді.
