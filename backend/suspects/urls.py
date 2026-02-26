from django.urls import path
from . import views

urlpatterns = [
    path('suspects/', views.SuspectListCreateView.as_view(), name='suspect-list-create'),
    path('suspects/high-priority/', views.SuspectHighPriorityListView.as_view(), name='suspect-high-priority'),
    path('most-wanted/', views.MostWantedPublicListView.as_view(), name='most-wanted-public'),
    path('suspects/<int:pk>/', views.SuspectDetailView.as_view(), name='suspect-detail'),
    path('suspects/<int:pk>/supervisor-review/', views.SuspectSupervisorReviewView.as_view(), name='suspect-supervisor-review'),
    path('interrogations/', views.InterrogationListCreateView.as_view(), name='interrogation-list-create'),
    path('interrogations/<int:pk>/captain-decision/', views.InterrogationCaptainDecisionView.as_view(), name='interrogation-captain-decision'),
    path('interrogations/<int:pk>/chief-confirm/', views.InterrogationChiefConfirmView.as_view(), name='interrogation-chief-confirm'),
    path('arrest-orders/', views.ArrestOrderListCreateView.as_view(), name='arrest-order-list-create'),
]
