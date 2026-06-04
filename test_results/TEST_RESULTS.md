# Результаты нагрузочного тестирования

Тестирование было проведено с помощью утилиты Apache Benchmark, количество запросов: 1000, конкурентность: 10

### Сценарий измерения 1: Статика через Nginx

Requests per second:    5745.08 [#/sec] (mean)
Time per request:       1.741 [ms] (mean)

### Сценарий измерения 2: Статика через Gunicorn

Requests per second:    472.29 [#/sec] (mean)
Time per request:       21.174 [ms] (mean)

### Сценарий измерения 3: Динамика через Gunicorn

Requests per second:    5.41 [#/sec] (mean)
Time per request:       1848.100 [ms] (mean)

### Сценарий измерения 4: Динамика через Nginx без кеша

Requests per second:    2913.19 [#/sec] (mean)
Time per request:       3.433 [ms] (mean)

### Сценарий измерения 5: Динамика через Nginx с кешем

Requests per second:    4794.67 [#/sec] (mean)
Time per request:       2.086 [ms] (mean)

# Ответы на вопросы

### 1. Насколько быстрее отдается статика по сравнению с WSGI?

Статика Nginx: 5745.08 [#/sec]
Статика Gunicorn: 472.29 [#/sec]

Статика через Nginx в сравнении с WSGi отдается быстрее примерно в 12,16 раз.

### 2. Во сколько раз ускоряет работу proxy_cache?

Без кеша: 2913.19 [#/sec]
C кешем: 4794.67 [#/sec]

Proxy_cache ускоряет работу примерно в 1,64 раза.
