# Додавання нових моделей (Stage 1+)

## Основне правило: існуючі таблиці — `managed = False`

Всі моделі, що映射 існуючі таблиці Supabase, повинні мати `Meta.managed = False`:

```python
class MyExistingModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # ... поля ...
    
    class Meta:
        managed = False
        db_table = 'existing_table_name'
```

Це гарантує, що Django міграції НЕ створюватимуть, не змінюватимуть і не видалятимуть цю таблицю.

---

## 1. Додавання НОВОЇ таблиці (Django-managed)

### Крок 1: Створи модель у потрібній app

Приклад: додай нову таблицю `document_reviews` в `apps/files/models.py`:

```python
class DocumentReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # НЕ додавай managed = False для НОВИХ моделей!
        db_table = 'document_reviews'
        unique_together = ('document', 'reviewer')
```

### Крок 2: Зареєструй в admin.py

```python
@admin.register(DocumentReview)
class DocumentReviewAdmin(admin.ModelAdmin):
    list_display = ('document', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('document__title', 'reviewer__email')
```

### Крок 3: Створи міграцію

```bash
python manage.py makemigrations apps.files
```

Перевір згенеровану міграцію в `apps/files/migrations/XXXX_auto.py`:

```bash
python manage.py sqlmigrate apps.files 0002  # Перевір SQL
```

### Крок 4: Застосуй міграцію

```bash
python manage.py migrate apps.files
```

---

## 2. Розширення ІСНУЮЧОЇ таблиці (додавання нового поля)

### ⚠️ ВАЖЛИВО: Тільки додатки, БЕЗ видалення!

Якщо треба додати поле в існуючу таблицю, наприклад в `chat_members`:

```python
class ChatMember(models.Model):
    # ... існуючі поля ...
    joined_at = models.DateTimeField(auto_now_add=True, default=timezone.now)  # НОВЕ
    
    class Meta:
        managed = False
        db_table = 'chat_members'
```

Потім:

```bash
python manage.py makemigrations apps.chats
python manage.py sqlmigrate apps.chats 0001
python manage.py migrate apps.chats
```

---

## 3. Перевірка міграцій (важливо!)

Перед `migrate` завжди дивись на SQL:

```bash
python manage.py sqlmigrate apps.files 0002
```

**Забороненні операції в SQL:**
- `DROP TABLE` ❌
- `DROP COLUMN` ❌
- `ALTER TABLE ... DROP` ❌
- `TRUNCATE TABLE` ❌
- Зміни `PRIMARY KEY` чи `UNIQUE` constraints ❌

**Дозволені операції:**
- `CREATE TABLE` (для НОВИХ таблиць) ✅
- `ALTER TABLE ... ADD COLUMN` ✅
- `ALTER TABLE ... ADD CONSTRAINT` ✅
- Індекси та нові констрейнти ✅

Якщо міграція містить щось заборонене — видаліть її:

```bash
python manage.py migrate apps.files 0001  # откат
rm apps/files/migrations/0002_*.py  # видалити файл
```

---

## 4. Як писати безпечні міграції вручну

Якщо `makemigrations` щось грубо роман, напиши міграцію вручну:

```python
# apps/files/migrations/0003_add_review_status.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('files', '0002_documentreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentreview',
            name='status',
            field=models.CharField(max_length=50, default='pending'),
        ),
    ]
```

---

## 5. Статус моделей

| Модель | Таблиця | managed | Примітка |
|--------|---------|---------|----------|
| User | users | False | Існуюча Supabase таблиця |
| Chat | chats | False | Існуюча Supabase таблиця |
| Message | messages | False | Існуюча Supabase таблиця |
| Document | documents | False | Існуюча Supabase таблиця |
| DocumentChunk | document_chunks | False | Існуюча Supabase таблиця |
| ChunkEmbedding | chunk_embeddings | False | Існуюча Supabase таблиця |
| ChatMember | chat_members | False | Існуюча Supabase таблиця |
| ChatAccess | chat_access | False | Існуюча Supabase таблиця |

---

## 6. Workflow для нових фіч

1. Дизайн схеми (SQL DDL)
2. Створи Django модель з `managed = True` (за замовченням)
3. `makemigrations` → перевір SQL → `migrate`
4. Тести + документація

---

## 7. Если щось пішло не так

Откатути все:

```bash
python manage.py migrate apps.files zero  # видалить ВСІ таблиці цієї app (не підходить для managed=False!)
```

**Безпечніше:**

1. Видалити нові мігра
ції вручну (файли в `migrations/`)
2. Один раз застосувати `migrate --fake` з коректною міграцією

```bash
python manage.py migrate apps.files --fake
```

---

## Корисні команди

```bash
# Показати всі міграції
python manage.py showmigrations

# Показати SQL для міграції
python manage.py sqlmigrate apps.files 0002

# Переглянути стан БД
python manage.py dbshell  # PostgreSQL shell

# Тест моделі
python manage.py shell
>>> from apps.users.models import User
>>> User.objects.all()
```
