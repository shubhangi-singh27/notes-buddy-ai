from django.urls import path
from documents.views.views_summary_history import SummaryHistoryView

urlpatterns = [
    path('<int:document_id>/summary-history/', SummaryHistoryView.as_view(), name='summary_history'),
]