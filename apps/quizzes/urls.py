from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('start/<uuid:arena_pk>/', views.start_quiz_view, name='start'),
    path('take/<uuid:pk>/', views.take_quiz_view, name='take'),
    path('take/<uuid:pk>/submit/', views.submit_quiz_view, name='submit'),
    path('attempts/<uuid:pk>/', views.attempt_result_view, name='attempt_result'),
    path('attempts/<uuid:pk>/grade/<uuid:answer_pk>/', views.self_grade_answer_api, name='self_grade'),
    path('history/', views.attempt_history_view, name='history'),
]

