from django.urls import path
from . import views

urlpatterns = [
    path('bail/', views.BailPaymentListCreateView.as_view(), name='bail-list-create'),
    path('bail/<int:pk>/approve/', views.BailPaymentSupervisorApproveView.as_view(), name='bail-approve'),
    path('fines/', views.FinePaymentListCreateView.as_view(), name='fine-list-create'),
    path('callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),
]









# from django.urls import path
# from . import views

# urlpatterns = [
#     path('bail/', views.BailPaymentListCreateView.as_view(), name='bail-list-create'),
#     path('bail/<int:pk>/approve/', views.BailPaymentSupervisorApproveView.as_view(), name='bail-approve'),
#     path('fines/', views.FinePaymentListCreateView.as_view(), name='fine-list-create'),
# ]
