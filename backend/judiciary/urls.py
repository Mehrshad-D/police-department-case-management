from django.urls import path
from . import views

urlpatterns = [
    path('trials/', views.TrialListCreateView.as_view(), name='trial-list-create'),
    path('trials/<int:pk>/', views.TrialDetailView.as_view(), name='trial-detail'),
    path('trials/<int:pk>/full/', views.TrialFullDetailView.as_view(), name='trial-full-detail'),
    path('trials/full-by-case/<int:case_id>/', views.TrialFullDataByCaseView.as_view(), name='trial-full-by-case'),
    path('verdicts/', views.VerdictListCreateView.as_view(), name='verdict-list-create'),
]
