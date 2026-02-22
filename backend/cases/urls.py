from django.urls import path
from . import views

urlpatterns = [
    path('cases/', views.CaseListCreateView.as_view(), name='case-list-create'),
    path('cases/crime-scene/', views.CrimeSceneCaseCreateView.as_view(), name='case-crime-scene-create'),
    path('cases/<int:pk>/', views.CaseDetailView.as_view(), name='case-detail'),
    path('complaints/', views.ComplaintListCreateView.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', views.ComplaintDetailView.as_view(), name='complaint-detail'),
    path('complaints/<int:pk>/correct/', views.ComplaintCorrectView.as_view(), name='complaint-correct'),
    path('complaints/<int:pk>/trainee-review/', views.ComplaintTraineeReviewView.as_view(), name='complaint-trainee-review'),
    path('complaints/<int:pk>/officer-review/', views.ComplaintOfficerReviewView.as_view(), name='complaint-officer-review'),
    path('crime-scene-reports/', views.CrimeSceneReportListCreateView.as_view(), name='crime-scene-list-create'),
    path('crime-scene-reports/<int:pk>/approve/', views.CrimeSceneReportApproveView.as_view(), name='crime-scene-approve'),
    path('cases/<int:case_pk>/complainants/', views.CaseComplainantListCreateView.as_view(), name='case-complainant-list-create'),
]
