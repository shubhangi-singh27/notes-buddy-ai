from django.urls import path, include
from documents.views.views import DocumentUploadView, DocumentListView, DocumentDetailView, DocumentDeleteView

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='upload_document'),
    path('delete/<int:document_id>/', DocumentDeleteView.as_view(), name='document_delete'),
    path('', include('documents.urls.urls_summary')),
    path('', include('documents.urls.urls_summary_history')),
    path('', DocumentListView.as_view(), name='list_documents'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document_detail'),
]