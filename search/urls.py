from django.urls import path
from .views import SemanticSearchView, AnswerView

urlpatterns = [
    path("semantic/", SemanticSearchView.as_view(), name="semantic_search"),
    path("answer/", AnswerView.as_view(), name="answer"),
]