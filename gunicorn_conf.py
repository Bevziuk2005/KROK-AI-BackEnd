import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
threads = 4
bind = '0.0.0.0:8000'
timeout = 120
