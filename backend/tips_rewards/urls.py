from django.urls import path
from . import views

urlpatterns = [
    path('tips/', views.TipListCreateView.as_view(), name='tip-list-create'),
    path('tips/<int:pk>/officer-review/', views.TipOfficerReviewView.as_view(), name='tip-officer-review'),
    path('tips/<int:pk>/detective-confirm/', views.TipDetectiveConfirmView.as_view(), name='tip-detective-confirm'),
    path('rewards/lookup/', views.RewardLookupView.as_view(), name='reward-lookup'),
    path('rewards/verify/', views.RewardVerifyView.as_view(), name='reward-verify'),
    path('rewards/redeem/', views.RewardRedeemView.as_view(), name='reward-redeem'),
]
