# Setup Instructions (After Clone)

Цей проєкт вже має базову структуру Django, всі моделі замаплені на існуючу Supabase БД, та налаштовану Microsoft 365 авторизацію.

## Quick Start (локально)

### 1. Клонування та залежності

```bash
git clone <repo>
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Налаштування середовища

Скопіюйте `.env.example` в `.env` та заповніть значення:

```bash
cp .env.example .env
# Відредагуйте .env:
# - DATABASE_URL (з Supabase)
# - MS_CLIENT_ID, MS_CLIENT_SECRET (з Azure)
# - OPENAI_API_KEY (з OpenAI)
# - SECRET_KEY (генеруйте свій або використайте приклад)
```

Приклад заповнення `.env`:
```
SECRET_KEY=your-super-secret-django-key-min-50-chars-here
DATABASE_URL=postgresql://user:pass@host.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
MS_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MS_CLIENT_SECRET=your_secret_here
MS_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MS_REDIRECT_URI=http://localhost:8000/api/v1/auth/microsoft/callback/
```

### 3. Міграції та адмін

```bash
python manage.py migrate
python manage.py createsuperuser --email admin@krok.edu.ua
```

### 4. Запуск dev-сервера

```bash
python manage.py runserver
```

Сервер доступний на `http://localhost:8000/`.

Адмін-панель: `http://localhost:8000/admin/`

Перевіряю здоров'я: `http://localhost:8000/health/`

## Структура проєкту

```
backend/
├── project/              # Django project settings
│   ├── settings/         # base.py, production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/           # User model, auth, JWT
│   ├── chats/           # Chat, Message models
│   ├── files/           # Document, RAG models
│   └── common/          # Utilities, health endpoint
├── requirements.txt     # Python dependencies
├── manage.py           # Django CLI
└── README.md           # Main docs
```

## Database

Існуюча Supabase схема вже замаплена:
- `users` → `User` model (managed=False)
- `chats` → `Chat`, `ChatMember`, `ChatAccess` models (managed=False)
- `messages` → `Message` model (managed=False)
- `documents`, `document_chunks`, `chunk_embeddings` → `Document`, `DocumentChunk`, `ChunkEmbedding` (managed=False)

Новіапаються таблиці (Django-managed):
- `django_refresh_tokens` → `RefreshToken` model (для JWT refresh tokens)

Усі існуючи таблиці залишаються неторканими (`Meta.managed = False`).

## API Endpoints

| Endpoint | Метод | Опис |
|----------|-------|------|
| `/health/` | GET | Health check |
| `/api/v1/auth/microsoft/login/` | POST | Запуск Microsoft OAuth2 login |
| `/api/v1/auth/microsoft/callback/` | GET | Microsoft redirect callback |
| `/api/v1/auth/microsoft/refresh/` | POST | Refresh JWT access token |
| `/api/v1/auth/logout/` | POST | Logout (revoke refresh token) |
| `/api/v1/auth/me/` | GET | Current user info |

## Docker (локально)

```bash
docker-compose up --build
```

Стартуються:
- Django web сервер на `http://localhost:8000`
- Redis на `localhost:6379`

## Тестування

```bash
pytest
```

## Deployment (Render.com)

1. Пуш на GitHub
2. На render.com: створити Web Service, підключити GitHub repo
3. Встановити environment variables (див. `.env.example`)
4. Render автоматично виконає build і deploy

Детальніше в `render.yaml`.

## Important Notes

⚠️ **Ніколи не комітьте `.env` — він містить секрети!**
- `.env` уже в `.gitignore`
- Використовуйте `.env.example` як шаблон

🔒 **Microsoft 365 авторизація:**
- Лише e-mail адреси `@krok.edu.ua` допускаються
- Необхідно створити App Registration в Microsoft Entra
- Встановити Redirect URI у Azure

🗄️ **База даних:**
- Усі існуючи Supabase таблиці захищені від видалення (managed=False)
- Для додавання нових таблиць див. `ADDING_MODELS.md`

## Контакти

За питаннями до документації див:
- `README.md` — основна інформація
- `ADDING_MODELS.md` — як додавати нові моделі
- `.env.example` — який env змінні потрібні
