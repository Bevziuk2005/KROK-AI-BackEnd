# 🚀 KROK-AI-BackEnd API - Frontend Integration Guide

**Base URL:** `https://krok-ai-back.onrender.com`

**API Version:** v1

---

## ✅ СТАТУС: ВСІ ENDPOINTS ТЕСТОВАНІ І ПРАЦЮЮТЬ

Всі endpoints описані нижче **100% готові до integration** на frontend.

---

## 📋 ТАБЛИЦЯ ВСІХ ENDPOINTS

| Endpoint | Method | Auth | Опис |
|----------|--------|------|------|
| [`/health/`](#health-check) | GET | ❌ | Перевірка здоров'я сервера |
| [`/api/v1/auth/login/`](#microsoft-oauth---login) | POST | ❌ | Отримати URL для Azure логіну |
| [`/api/v1/auth/callback/`](#microsoft-oauth---callback) | GET / POST | ❌ | Обміняти код на JWT токени |
| [`/api/v1/auth/refresh/`](#refresh-token) | POST | ❌ | Оновити access token |
| [`/api/v1/auth/logout/`](#logout) | POST | ✅ Auth | Вихід (revoke refresh token; потребує Authorization header) |
| [`/api/v1/users/me/`](#get-current-user) | GET | ✅ | Отримати інформацію про себе |
| [`/api/v1/users/me/`](#update-profile) | PATCH | ✅ | Оновити профіль |
| [`/api/v1/chats/`](#list-chats) | GET | ✅ | Список чатів користувача |
| [`/api/v1/chats/`](#create-chat) | POST | ✅ | Створити новий чат |
| [`/api/v1/chats/{id}/`](#get-chat) | GET | ✅ | Отримати деталі чату |
| [`/api/v1/chats/{id}/messages/`](#get-messages) | GET | ✅ | Отримати повідомлення чату |
| [`/api/v1/chats/{id}/messages/`](#send-message) | POST | ✅ | Відправити повідомлення |
| [`/api/v1/files/`](#list-documents) | GET | ✅ | Список завантажених файлів |
| [`/api/v1/files/upload/`](#files---upload-document) | POST | ✅ | Завантажити файл (автоматично запускає обробку) |
| [`/api/v1/rag/search/`](#rag-search) | POST | ✅ | Векторний пошук у файлах через pgvector |

---

## 🔐 АУТЕНТИФІКАЦІЯ

### JWT Tokens

Після логіну отримуєш два токена:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Використання в запитах

Додай до **всіх** authenticated запитів header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token Lifetime

- **access_token:** 15 хвилин
- **refresh_token:** 30 днів

### 🔒 Production Environment Variables

У production-середовищі варто задати такі змінні явно:

- `SECRET_KEY` — обов’язковий для Django; у production без нього піднімається `ImproperlyConfigured` під час старту.
- `CORS_ALLOWED_ORIGINS` — для production бажано задати список дозволених origin, розділений комами.
- `ALLOWED_HOSTS` — для production бажано задати список хостів, розділений комами.

У поточній конфігурації саме `SECRET_KEY` має явну перевірку на старті; для `CORS_ALLOWED_ORIGINS` і `ALLOWED_HOSTS` значення слід задати явно, щоб уникнути неочікуваних налаштувань у продакшні.

---

## 🌐 ЩО ПОКАЗУЄТЬСЯ ПРИ ПРЯМОМУ ПЕРЕХОДІ В БРАУЗЕРІ

Більшість ендпоінтів — це **POST-only API-роути** без фронтенд-сторінки. Якщо просто вставити посилання в адресний рядок (тобто зробити GET), браузер отримає:

| Посилання | Що покаже прямий GET-перехід |
|---|---|
| `/health/` | JSON `{"status": "healthy"}` — працює і в браузері, бо це GET-ендпоінт |
| `/api/v1/auth/login/` | **405 Method Not Allowed** (DRF Browsable API покаже форму для POST-запиту, якщо `DEBUG=True`, або чистий 405 JSON у продакшн-режимі) |
| `/api/v1/auth/callback/?code=...` | HTML-сторінка зі спінером → редірект на `/dashboard` (реальний сценарій після логіну в Azure) |
| `/api/v1/auth/callback/` (без `?code=`) | HTML-сторінка з помилкою "Missing code", статус 400 |
| `/api/v1/auth/refresh/` | 405 Method Not Allowed (тільки POST) |
| `/api/v1/auth/logout/` | 405 Method Not Allowed (тільки POST) |
| `/api/v1/users/me/` | 401 Unauthorized (без токена) — GET підтримується, але потребує `Authorization: Bearer ...` |
| `/api/v1/chats/` | 401 Unauthorized без токена; з токеном — JSON список чатів |
| `/api/v1/chats/{id}/messages/` | Підтримує і GET, і POST (кастомний `@action`) — з токеном покаже список повідомлень |
| `/api/v1/files/` | 401 Unauthorized без токена (⚠️ реальний шлях — `/files/`, не `/documents/`, див. нижче) |
| `/api/v1/rag/search/` | 405 Method Not Allowed на GET (тільки POST) |
| `/admin/` | Стандартна Django admin-сторінка логіну |

⚠️ **Важлива розбіжність:** у попередній версії цього README фігурував шлях `/api/v1/documents/` — за фактичним `apps/files/urls.py` роут зареєстровано як **`/api/v1/files/`** (`router.register(r'files', FileViewSet)`). У цій версії всі приклади вже виправлено на `/api/v1/files/`.

---

## 📌 ENDPOINTS (ДЕТАЛЬНО)

### HEALTH CHECK

#### GET `/health/`

Перевірка що сервер живий.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/health/
```

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

## 🔐 MICROSOFT OAUTH - LOGIN

#### POST `/api/v1/auth/login/`

Отримати URL для редіректу на Azure логін.

> Новий контракт: `redirect` у POST `/login/` — це не `redirect_uri` для Azure. Це поле означає кінцевий фронтенд URL, куди користувач має потрапити після успішної авторизації. Бекенд сам гарантує, що Azure отримає фіксований `redirect_uri` із `settings.MS_REDIRECT_URI`, а бажаний фронтенд URL передається через `state`.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "redirect": "https://bevziuk2005.github.io/KROK-AI-FrontEnd/dashboard"
  }'
```

**Response (200 OK):**
```json
{
  "auth_url": "https://login.microsoftonline.com/xxx/oauth2/v2.0/authorize?client_id=xxx&redirect_uri=https%3A%2F%2Fkrok-ai-back.onrender.com%2Fapi%2Fv1%2Fauth%2Fcallback%2F&state=..."
}
```

**Що робити:**
1. Отримай `auth_url` з відповіді.
2. Редірегуй користувача на цей URL.
3. Azure поверне користувача на бекенд `redirect_uri` з `code` та `state`.
4. Бекенд обміняє код на токени, перевірить `state`, і завершить редірект до дозволеного фронтенд-URL.

**Безпека:**
- `redirect_uri` для Azure завжди фіксований і не береться з тіла запиту.
- `redirect` використовується лише для формування `state`.
- Дозволений список фронтенд-доменів визначається через `ALLOWED_FRONTEND_REDIRECTS`.
- Якщо `state` відсутній або невалідний — використовується `FRONTEND_DEFAULT_REDIRECT`.

---

## 🔐 MICROSOFT OAUTH - CALLBACK

#### GET / POST `/api/v1/auth/callback/`

Обміняти Azure код на JWT токени. **Це де користувач реєструється!**

⚠️ **Важливо:** ендпоінт має ДВІ різні поведінки залежно від методу — це не просто "той самий" запит у двох варіантах.

---

**GET `/api/v1/auth/callback/?code=...`** — основний сценарій (production)

Це той URL, на який Azure AD **реально редіректить браузер користувача** після логіну (`response_mode=query`, тому Azure додає `?code=...` до фіксованого backend `redirect_uri` і робить GET). Важливо: `redirect_uri` для Azure завжди дорівнює `settings.MS_REDIRECT_URI` і не залежить від `redirect` у POST `/login/`.

Що відбувається на сервері:
1. Бере `code` з query-параметра.
2. Обмінює його на `id_token` через Microsoft token endpoint, використовуючи той самий фіксований backend `redirect_uri`.
3. Декодує `state` і отримує бажаний фронтенд URL, перевіряє його проти `ALLOWED_FRONTEND_REDIRECTS`.
4. Валідує `id_token` і перевіряє домен пошти (має бути `@KROK_DOMAIN`).
5. Створює/оновлює користувача, генерує `access_token` і `refresh_token`.
6. Повертає **не JSON, а готову HTML-сторінку** (`text/html`), яка:
   - показує спінер "Логіну вас..."
   - JS-скриптом кладе токени в `localStorage`
   - через 1 секунду редіректить на отриманий фронтенд URL (або `FRONTEND_DEFAULT_REDIRECT`, якщо `state` невалідний)

**Як працює `state`:**
- У POST `/login/` frontend передає бажаний URL у полі `redirect`.
- Бекенд безпечно кодує його в `state`.
- Azure повертає `state` назад у query params callback'у.
- Бекенд розкодовує `state` і використовує його лише для фінального редіректу на фронтенд.

**Що покаже прямий перехід за посиланням без `?code=...`** (як у вашому запиті):
HTML-сторінка з повідомленням про помилку (⚠️ **"Помилка входу"**, текст `Missing code`), статус **400 Bad Request**, і кнопка "Спробувати знову" (веде на `/login`). Тобто ніякого JSON — просто сторінка помилки, бо `code` беруть із query, а Azure ще не встиг його підставити.

Приклад HTML-відповіді при помилці:
```
⚠️ Помилка входу
Missing code
На жаль, не вдалося вас авторізувати
[Спробувати знову]
```

Аналогічно HTML з помилкою повертається і якщо:
- обмін коду на токен не вдався (`Token exchange failed: ...`)
- `id_token` невалідний (`Invalid token: ...`)
- email не з дозволеного домену (`Email domain not allowed. Use @...`)
- будь-яка інша непередбачена помилка (`Unexpected error: ...`)

---

**POST `/api/v1/auth/callback/`** — залишено для зворотної сумісності (наприклад, якщо фронтенд сам забирає `code` з URL і шле його напряму)

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/callback/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "M.R3_BAY...",
    "redirect": "https://your-frontend.com/auth/callback"
  }'
```

**Response (200 OK, JSON):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Помилки (JSON, на відміну від GET-варіанту):**

```json
// Код не передано (400)
{ "detail": "Missing code" }

// Обмін коду на токен не вдався (400)
{ "detail": "Token exchange failed", "error": "..." }

// Email домен не дозволений (403)
{ "detail": "Email domain not allowed" }

// Невалідний токен (400)
{ "detail": "Invalid id_token", "error": "..." }
```

**Що робити (фронтенд):**
- Якщо у вас класичний SPA-фронтенд на окремому домені — використовуйте **POST** і самі керуйте токенами та редіректом.
- Якщо `redirect_uri` в Azure App Registration вказує прямо на бекенд (`.../api/v1/auth/callback/`) — спрацює **GET**-сценарій, і бекенд сам віддасть HTML зі збереженням токенів у `localStorage` та редіректом на `/dashboard` (це поточна production-конфігурація на Render).

---

## 🔄 REFRESH TOKEN

#### POST `/api/v1/auth/refresh/`

Оновити `access_token` використовуючи `refresh_token`.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Помилки:**

```json
// Token не передано (400)
{ "detail": "Missing refresh token" }

// Token невалідний (401)
{ "detail": "Invalid refresh token" }
```

---

## 🚪 LOGOUT

#### POST `/api/v1/auth/logout/`

Вихід — відкликання refresh token для поточного користувача. Endpoint потребує валідний JWT в заголовку `Authorization: Bearer ...`.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/logout/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "detail": "Logged out"
}
```

Якщо у тілі передано `refresh_token`, він буде відкликаний лише для поточного користувача. Якщо токен не передано, backend відкликає всі активні refresh tokens цього користувача.

---

## 👤 GET CURRENT USER

#### GET `/api/v1/users/me/`

Отримати інформацію про поточного користувача.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/api/v1/users/me/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@krok.edu.ua",
  "created_at": "2026-06-11T16:53:41Z",
  "updated_at": "2026-06-11T16:53:41Z"
}
```

---

## 📝 UPDATE PROFILE

#### PATCH `/api/v1/users/me/`

Оновити профіль користувача.

**Request:**
```bash
curl -X PATCH https://krok-ai-back.onrender.com/api/v1/users/me/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ivan",
    "last_name": "Kovalenko"
  }'
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@krok.edu.ua",
  "first_name": "Ivan",
  "last_name": "Kovalenko",
  "created_at": "2026-06-11T16:53:41Z",
  "updated_at": "2026-06-11T16:53:41Z"
}
```

---

## 💬 CHATS - LIST CHATS

#### GET `/api/v1/chats/`

Отримати список всіх чатів користувача.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/api/v1/chats/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "General Discussion",
      "type": "general",
      "owner": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-06-11T10:00:00Z",
      "updated_at": "2026-06-11T15:30:00Z"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "title": "Project Planning",
      "type": "project",
      "owner": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-06-10T09:00:00Z",
      "updated_at": "2026-06-11T14:20:00Z"
    }
  ]
}
```

**Query Parameters:**
```
?page=1              # Номер сторінки (default: 1)
?page_size=20        # Кількість на сторінці (default: 20, max: 100)
```

---

## ➕ CHATS - CREATE CHAT

#### POST `/api/v1/chats/`

Створити новий чат.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/chats/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Discussion",
    "type": "general"
  }'
```

**Response (201 Created):**
```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "title": "AI Discussion",
  "type": "general",
  "owner": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-06-11T16:53:41Z",
  "updated_at": "2026-06-11T16:53:41Z"
}
```

---

## 📖 CHATS - GET CHAT

#### GET `/api/v1/chats/{id}/`

Отримати деталі конкретного чату.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/api/v1/chats/123e4567-e89b-12d3-a456-426614174000/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "General Discussion",
  "type": "general",
  "owner": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-06-11T10:00:00Z",
  "updated_at": "2026-06-11T15:30:00Z"
}
```

---

## 💬 MESSAGES - GET MESSAGES

#### GET `/api/v1/chats/{chat_id}/messages/`

Отримати повідомлення з чату.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/api/v1/chats/123e4567-e89b-12d3-a456-426614174000/messages/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200 OK):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "423e4567-e89b-12d3-a456-426614174003",
      "chat": "123e4567-e89b-12d3-a456-426614174000",
      "user": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "Hello, how are you?",
      "token_count": 5,
      "created_at": "2026-06-11T15:00:00Z"
    },
    {
      "id": "523e4567-e89b-12d3-a456-426614174004",
      "chat": "123e4567-e89b-12d3-a456-426614174000",
      "user": null,
      "role": "assistant",
      "content": "I'm doing well, thank you for asking!",
      "token_count": 8,
      "created_at": "2026-06-11T15:01:00Z"
    }
  ]
}
```

---

## ✉️ MESSAGES - SEND MESSAGE

#### POST `/api/v1/chats/{chat_id}/messages/`

Отправити повідомлення в чат.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/chats/123e4567-e89b-12d3-a456-426614174000/messages/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "What is the capital of France?",
    "token_count": 8
  }'
```

**Response (201 Created):**
```json
{
  "id": "623e4567-e89b-12d3-a456-426614174005",
  "chat": "123e4567-e89b-12d3-a456-426614174000",
  "user": "550e8400-e29b-41d4-a716-446655440000",
  "role": "user",
  "content": "What is the capital of France?",
  "token_count": 8,
  "created_at": "2026-06-11T16:00:00Z"
}
```

**Параметри:**
- `role`: "user" або "assistant"
- `content`: Текст повідомлення
- `token_count`: Кількість токенів (опціонально)

---

## 📁 FILES - LIST DOCUMENTS

#### GET `/api/v1/files/`

Отримати список завантажених документів.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/api/v1/files/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "723e4567-e89b-12d3-a456-426614174006",
      "title": "Project Plan.txt",
      "storage_key": "550e8400/20260611165341_Project Plan.txt",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-06-11T16:53:41Z",
      "updated_at": "2026-06-11T16:54:00Z"
    }
  ]
}
```

**Статуси документу:**
- `pending` - Очікує обробки
- `processing` - Обробляється (витяг тексту, embeddings)
- `completed` - Готовий до RAG пошуку
- `failed` - Помилка при обробці (див. `error_message`)

---

## ⬆️ FILES - UPLOAD DOCUMENT

#### POST `/api/v1/files/upload/`

Завантажити файл для RAG. Після збереження документу обробка стартує автоматично через `process_document_background(doc.id)`.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/files/upload/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "file=@document.txt" \
  -F "title=My Document"
```

**Response (201 Created):**
```json
{
  "id": "823e4567-e89b-12d3-a456-426614174007",
  "title": "My Document",
  "storage_key": "550e8400/20260611165341_document.txt",
  "status": "pending",
  "error_message": null,
  "created_at": "2026-06-11T16:53:41Z",
  "updated_at": "2026-06-11T16:53:41Z"
}
```

**Опційний ре-трай обробки:**
- Якщо документ впав у `failed`, можна вручну повторити обробку через `POST /api/v1/files/{id}/process/`.
- Для нових upload це робити не потрібно — обробка вже запускається автоматично.

**Обмеження:**
- Дозволені типи: `text/plain`, `text/markdown`, `application/pdf`
- Максимум 10 MB
- Для текстових файлів очікується UTF-8; для PDF текст витягується перед чанкінгом

---

## 🔍 RAG - SEARCH

#### POST `/api/v1/rag/search/`

Векторний пошук у завантажених документах через pgvector (embeddings + cosine distance у PostgreSQL).

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/rag/search/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the project deadlines?",
    "top_k": 5
  }'
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "similarity": 0.89,
      "chunk_id": "923e4567-e89b-12d3-a456-426614174008",
      "chunk_index": 2,
      "chunk_text": "The project deadline is December 31st, 2026",
      "document_id": "823e4567-e89b-12d3-a456-426614174007"
    },
    {
      "similarity": 0.76,
      "chunk_id": "a23e4567-e89b-12d3-a456-426614174009",
      "chunk_index": 5,
      "chunk_text": "Milestone 1 is due on June 30th",
      "document_id": "823e4567-e89b-12d3-a456-426614174007"
    }
  ]
}
```

**Параметри:**
- `query`: Пошуковий запит (обов'язковий)
- `top_k`: Кількість результатів (default: 5, max: 20)

---

## ⚠️ ERROR RESPONSES

Усі endpoints повертають помилки в наступному форматі:

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid request data",
  "field_name": ["Error message"]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## 🧪 ТЕСТУВАННЯ ENDPOINTS

### БЫСТРИЙ ТЕСТ (без аутентифікації)

```bash
# 1. Перевіри сервер живий
curl https://krok-ai-back.onrender.com/health/

# Повинна повернути:
# {"status":"healthy"}
```

### ПОВНИЙ ТЕСТ (з аутентифікацією)

```bash
# 1. Отримай auth URL
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{}'

# 2. В браузері відкрий auth_url
# 3. Логін з корпоративною поштою
# 4. Azure редірегує назад з code
# 5. Обміняй код на токени
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/callback/ \
  -H "Content-Type: application/json" \
  -d '{"code":"[CODE_FROM_AZURE]"}'

# 6. Отримай себе
curl https://krok-ai-back.onrender.com/api/v1/users/me/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]"
```

---

## 📱 FRONTEND IMPLEMENTATION TIPS

### 1. Storage Tokens
```javascript
// Збережи токени
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);

// Читай токени
const token = localStorage.getItem('access_token');
```

### 2. Axios Setup
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://krok-ai-back.onrender.com',
});

// Додай token до всіх запитів
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh при 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token');
      const response = await api.post('/api/v1/auth/refresh/', {
        refresh_token: refresh,
      });
      localStorage.setItem('access_token', response.data.access_token);
      // Retry original request
      return api(error.config);
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 3. OAuth Flow
```javascript
// Step 1: Отримай auth URL
const { data } = await api.post('/api/v1/auth/login/', {
  redirect: window.location.href + '/auth/callback',
});

// Step 2: Редірегуй
window.location.href = data.auth_url;

// Step 3: На /auth/callback сторінці
const code = new URLSearchParams(window.location.search).get('code');
const { data: tokens } = await api.post('/api/v1/auth/callback/', {
  code,
  redirect: window.location.href,
});

// Step 4: Збережи токени
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);
```

---

## ✅ CHECKLIST FOR FRONTEND DEVELOPER

```
□ Endpoint /health/ працює (curl test)
□ OAuth login flow розумію
□ Создал axios instance з auto-retry
□ Чату список завантажується
□ Можу відправити повідомлення
□ Можу завантажити документ
□ RAG search працює
□ Токени зберігаються правильно
□ Refresh автоматичний при 401
□ Logout видаляє токени
□ Всі errors обробляються
```

---

**READY FOR PRODUCTION! 🚀**

Всі endpoints тестовані і готові до integration.
