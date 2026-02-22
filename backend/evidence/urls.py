from django.urls import path
from . import views

urlpatterns = [
    path('evidence/', views.EvidenceListCreateView.as_view(), name='evidence-list-create'),
    path('evidence/<int:pk>/', views.EvidenceDetailView.as_view(), name='evidence-detail'),
    path('evidence/<int:pk>/biological-review/', views.BiologicalEvidenceReviewView.as_view(), name='biological-review'),
    path('evidence/<int:pk>/biological-add-image/', views.BiologicalEvidenceAddImageView.as_view(), name='biological-add-image'),
    path('cases/<int:case_pk>/evidence-links/', views.EvidenceLinkListCreateView.as_view(), name='evidence-link-list-create'),
    path('cases/<int:case_pk>/evidence-links/<int:pk>/', views.EvidenceLinkDetailView.as_view(), name='evidence-link-detail'),
]
