import multiprocessing
import os

workers = multiprocessing.cpu_count() * 2 + 1
threads = 4

# Использовать PORT из environment переменной, если есть (Render)
# Или default 8000 для локальной разработки
port = os.getenv('PORT', '8000')
bind = f'0.0.0.0:{port}'

timeout = 120