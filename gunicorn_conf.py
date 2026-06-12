import multiprocessing
import os

workers = 1
threads = 2

# Использовать PORT из environment переменной, если есть (Render)
# Или default 8000 для локальной разработки
port = os.getenv('PORT', '8000')
bind = f'0.0.0.0:{port}'

timeout = 120
