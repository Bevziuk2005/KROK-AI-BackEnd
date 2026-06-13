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
| [`/api/v1/auth/callback/`](#microsoft-oauth---callback) | POST | ❌ | Обміняти код на JWT токени |
| [`/api/v1/auth/refresh/`](#refresh-token) | POST | ❌ | Оновити access token |
| [`/api/v1/auth/logout/`](#logout) | POST | ✅ | Вихід (revoke refresh token) |
| [`/api/v1/users/me/`](#get-current-user) | GET | ✅ | Отримати інформацію про себе |
| [`/api/v1/users/me/`](#update-profile) | PATCH | ✅ | Оновити профіль |
| [`/api/v1/chats/`](#list-chats) | GET | ✅ | Список чатів користувача |
| [`/api/v1/chats/`](#create-chat) | POST | ✅ | Створити новий чат |
| [`/api/v1/chats/{id}/`](#get-chat) | GET | ✅ | Отримати деталі чату |
| [`/api/v1/chats/{id}/messages/`](#get-messages) | GET | ✅ | Отримати повідомлення чату |
| [`/api/v1/chats/{id}/messages/`](#send-message) | POST | ✅ | Відправити повідомлення |
| [`/api/v1/documents/`](#list-documents) | GET | ✅ | Список завантажених файлів |
| [`/api/v1/documents/`](#upload-document) | POST | ✅ | Завантажити файл |
| [`/api/v1/rag/search/`](#rag-search) | POST | ✅ | Семантичний пошук у файлах |

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

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "redirect": "https://your-frontend.com/auth/callback"
  }'
```

**Response (200 OK):**
```json
{
  "auth_url": "https://login.microsoftonline.com/xxx/oauth2/v2.0/authorize?client_id=xxx&..."
}
```

**Що робити:**
1. Отримай `auth_url` з відповіді
2. Редірегуй користувача на цей URL
3. Користувач логіниться в Azure
4. Azure редірегує назад з `code` параметром

---

## 🔐 MICROSOFT OAUTH - CALLBACK

#### POST `/api/v1/auth/callback/`

Обміняти Azure код на JWT токени. **Це де користувач реєструється!**

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/callback/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "M.R3_BAY...",
    "redirect": "https://your-frontend.com/auth/callback"
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Помилки:**

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

**Що робити:**
1. Отримай `code` з URL параметра (Azure редірегує сюди)
2. Відправи POST запит з кодом
3. Отримай `access_token` та `refresh_token`
4. Збережи токени (localStorage або cookie)
5. Редірегуй користувача на главну сторінку

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

Вихід - рівокувати refresh token.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/auth/logout/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Response (200 OK):**
```json
{
  "detail": "Logged out successfully"
}
```

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

#### GET `/api/v1/documents/`

Отримати список завантажених документів.

**Request:**
```bash
curl https://krok-ai-back.onrender.com/api/v1/documents/ \
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

#### POST `/api/v1/documents/`

Завантажити текстовий файл для RAG.

**Request:**
```bash
curl -X POST https://krok-ai-back.onrender.com/api/v1/documents/ \
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

**Обмеження:**
- Тільки `.txt` файли
- Максимум 10 MB
- Мають бути UTF-8 encoded

---

## 🔍 RAG - SEARCH

#### POST `/api/v1/rag/search/`

Семантичний пошук у завантажених документах.

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
      "document_id": "823e4567-e89b-12d3-a456-426614174007",
      "document_title": "My Document"
    },
    {
      "similarity": 0.76,
      "chunk_id": "a23e4567-e89b-12d3-a456-426614174009",
      "chunk_index": 5,
      "chunk_text": "Milestone 1 is due on June 30th",
      "document_id": "823e4567-e89b-12d3-a456-426614174007",
      "document_title": "My Document"
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

## 📞 КОНТАКТИ / ПІДТРИМКА

**Backend:** https://krok-ai-back.onrender.com  
**GitHub:** https://github.com/Bevziuk2005/KROK-AI-BackEnd  
**Issues:** https://github.com/Bevziuk2005/KROK-AI-BackEnd/issues

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
