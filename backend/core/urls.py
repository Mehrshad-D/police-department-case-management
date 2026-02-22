from django.urls import path
from . import views

urlpatterns = [
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
]
