from django.urls import path
from . import views

app_name = 'arenas'

urlpatterns = [
    path('', views.arena_list_view, name='list'),
    path('create/', views.arena_create_view, name='create'),
    path('<uuid:pk>/', views.arena_detail_view, name='detail'),
    path('<uuid:pk>/update/', views.arena_update_view, name='update'),
    path('<uuid:pk>/delete/', views.arena_delete_view, name='delete'),
    path('<uuid:pk>/upload/', views.document_upload_view, name='upload'),
    path('<uuid:pk>/documents/<uuid:doc_pk>/delete/', views.document_delete_view, name='document_delete'),
    path('<uuid:pk>/tasks/<str:task_id>/status/', views.task_status_api, name='task_status'),
]

