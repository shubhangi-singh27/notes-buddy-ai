from rest_framework import serializers
from documents.models import SummaryHistory

class SummaryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryHistory
        fields = [
            "id",
            "short_summary",
            "detailed_summary",
            "created_at"
        ]