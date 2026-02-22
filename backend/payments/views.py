"""
Bail payment (level 2-3 suspects; level 3 requires supervisor approval). Payment gateway integration placeholder.
"""
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import BailPayment, FinePayment
from .serializers import BailPaymentSerializer, BailPaymentCreateSerializer, FinePaymentSerializer
from accounts.permissions import IsSupervisor
from core.utils import log_audit


class BailPaymentListCreateView(generics.ListCreateAPIView):
    """List/create bail payments. Level 3 requires supervisor approval."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BailPayment.objects.filter(suspect__user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BailPaymentCreateSerializer
        return BailPaymentSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        bail = serializer.save(status=BailPayment.STATUS_PENDING)
        case = bail.suspect.case
        
        # Assuming case severity strings are standard: 'level_1', 'level_2', 'level_3', 'crisis'
        if getattr(case, 'severity', '') == 'level_3':
            bail.status = BailPayment.STATUS_SUPERVISOR_APPROVAL_NEEDED
        else:
            bail.status = BailPayment.STATUS_APPROVED
        bail.save()


class BailPaymentSupervisorApproveView(APIView):
    """Supervisor approves bail (level 3)."""
    permission_classes = [IsAuthenticated, IsSupervisor]

    @transaction.atomic
    def post(self, request, pk):
        bail = get_object_or_404(BailPayment, pk=pk)
        if bail.status != BailPayment.STATUS_SUPERVISOR_APPROVAL_NEEDED:
            return Response(
                {'success': False, 'error': {'message': 'Not pending supervisor approval.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bail.status = BailPayment.STATUS_APPROVED
        bail.approved_by_supervisor = request.user
        bail.approved_at = timezone.now()
        bail.save()
        log_audit(request.user, 'approve', 'BailPayment', bail.pk, 'Bail approved')
        return Response({'success': True, 'data': BailPaymentSerializer(bail).data})


class FinePaymentListCreateView(generics.ListCreateAPIView):
    """List/create fine payments (payment gateway integration)."""
    permission_classes = [IsAuthenticated]
    serializer_class = FinePaymentSerializer

    def get_queryset(self):
        return FinePayment.objects.filter(payer=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(payer=self.request.user, status=FinePayment.STATUS_PENDING)


class GatewayCallbackMockView(APIView):
    """Mock endpoint to simulate gateway confirming the payment."""
    permission_classes = []  # Open webhook endpoint for gateway

    @transaction.atomic
    def post(self, request):
        ref = request.data.get('gateway_reference')
        success = request.data.get('success', True)
        
        if not ref:
            return Response({"error": "Missing reference"}, status=400)
            
        if ref.startswith('BAIL-'):
            payment = get_object_or_404(BailPayment, gateway_reference=ref)
        elif ref.startswith('FINE-'):
            payment = get_object_or_404(FinePayment, gateway_reference=ref)
        else:
            return Response({"error": "Invalid reference format"}, status=400)

        payment.status = payment.STATUS_COMPLETED if success else payment.STATUS_FAILED
        payment.gateway_response = request.data
        payment.save()
        
        return Response({"message": "Payment recorded successfully", "new_status": payment.status})




















# """
# Bail payment (level 2-3 suspects; level 3 requires supervisor approval). Payment gateway integration placeholder.
# """
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from django.shortcuts import get_object_or_404
# from django.utils import timezone

# from .models import BailPayment, FinePayment
# from .serializers import BailPaymentSerializer, BailPaymentCreateSerializer, FinePaymentSerializer
# from accounts.permissions import IsSupervisor
# from core.utils import log_audit


# class BailPaymentListCreateView(generics.ListCreateAPIView):
#     """List/create bail payments. Level 3 requires supervisor approval."""
#     permission_classes = [IsAuthenticated]
#     serializer_class = BailPaymentSerializer

#     def get_queryset(self):
#         return BailPayment.objects.all().order_by('-created_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return BailPaymentCreateSerializer
#         return BailPaymentSerializer

#     def perform_create(self, serializer):
#         bail = serializer.save(status=BailPayment.STATUS_PENDING)
#         case = bail.suspect.case
#         if case.severity == case.SEVERITY_LEVEL_3:
#             bail.status = BailPayment.STATUS_SUPERVISOR_APPROVAL_NEEDED
#             bail.save()
#         else:
#             bail.status = BailPayment.STATUS_APPROVED
#             bail.save()


# class BailPaymentSupervisorApproveView(APIView):
#     """Supervisor approves bail (level 3)."""
#     permission_classes = [IsAuthenticated, IsSupervisor]

#     def post(self, request, pk):
#         bail = get_object_or_404(BailPayment, pk=pk)
#         if bail.status != BailPayment.STATUS_SUPERVISOR_APPROVAL_NEEDED:
#             return Response(
#                 {'success': False, 'error': {'message': 'Not pending supervisor approval.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         bail.status = BailPayment.STATUS_APPROVED
#         bail.approved_by_supervisor = request.user
#         bail.approved_at = timezone.now()
#         bail.save()
#         log_audit(request.user, 'approve', 'BailPayment', bail.pk, 'Bail approved')
#         return Response({'success': True, 'data': BailPaymentSerializer(bail).data})


# class FinePaymentListCreateView(generics.ListCreateAPIView):
#     """List/create fine payments (payment gateway integration)."""
#     permission_classes = [IsAuthenticated]
#     queryset = FinePayment.objects.all().order_by('-created_at')
#     serializer_class = FinePaymentSerializer

#     def perform_create(self, serializer):
#         serializer.save(payer=self.request.user, status=FinePayment.STATUS_PENDING)
