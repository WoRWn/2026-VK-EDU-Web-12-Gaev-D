bind = "0.0.0.0:8000"

workers = 2

wsgi_app = "application.wsgi:application"

accesslog = "-"
errorlog = "-"
loglevel = "info"