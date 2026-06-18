from django.db import connection
from django.http import JsonResponse


def health_check(request):
    database = "ok"
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        database = "error"

    payload = {"status": "ok" if database == "ok" else "degraded", "database": database}
    status_code = 200 if database == "ok" else 503
    return JsonResponse(payload, status=status_code)
