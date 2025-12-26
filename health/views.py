from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connection
from django.conf import settings
from django.core.cache import cache
import redis
import os

class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        health_status = {
            "status": "ok",
            "checks": {}
        }
        overall_status = 200

        # DB check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "ok"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
            overall_status = 503

        # Redis/Cache check
        try:
            if hasattr(settings, 'CELERY_BROKER_URL') and settings.CELERY_BROKER_URL:
                cache.set("health_check", "ok", 10)
                cache.get("health_check")
                health_status["checks"]["redis"] = "ok"
            else:
                health_status["checks"]["redis"] = "not configured"
        except Exception as e:
            health_status["checks"]["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
            overall_status = 503

        # File System check
        try:
            if hasattr(settings, "MEDIA_ROOT"):
                media_path = settings.MEDIA_ROOT
                os.makedirs(media_path, exist_ok=True)
                test_file = os.path.join(media_path, ".health_check")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                health_status["checks"]["filesystem"] = "ok"
            else:
                health_status["checks"]["filesystem"] = "not configured"
        except Exception as e:
            health_status["checks"]["filesystem"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
            overall_status = 503

        if hasattr(settings, "OPENAI_API_KEY") and settings.OPENAI_API_KEY:
            health_status["checks"]["openai"] = "configured"
        else:
            health_status["checks"]["openai"] = "not configured"

        return Response(health_status, status=overall_status)