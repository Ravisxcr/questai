from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('<uuid:pk>/delete/', views.question_delete_view, name='delete'),
    path('arena/<uuid:arena_pk>/export/<str:format>/', views.export_questions_view, name='export'),
]

