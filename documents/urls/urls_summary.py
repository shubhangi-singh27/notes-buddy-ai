from django.urls import path
from documents.views.views_summary import DocumentSummaryView, RegenerateSummaryView

urlpatterns = [
    path('<int:document_id>/summary/', DocumentSummaryView.as_view(), name='document_summary'),
    path('<int:document_id>/summary/regenerate/', RegenerateSummaryView.as_view(), name='regenerate_summary'),
]