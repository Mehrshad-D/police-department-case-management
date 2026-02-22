"""
Tips: citizen submit; officer reviews -> detective confirms -> reward code.
Reward lookup by national_id + code (police).
"""
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Tip, Reward
from .serializers import TipListSerializer, TipCreateSerializer, RewardSerializer, RewardClaimLookupSerializer
from accounts.permissions import IsPoliceOfficer, IsDetective, IsOfficerOrAbove, has_any_role
from core.utils import log_audit, notify

User = get_user_model()


class TipListCreateView(generics.ListCreateAPIView):
    """List tips (filtered by role); citizen submits tip."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not has_any_role(user, ['Police Officer', 'Detective', 'Sergeant', 'Captain', 'Police Chief', 'System Administrator']):
            return Tip.objects.filter(submitter=user).order_by('-created_at')
        return Tip.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TipCreateSerializer
        return TipListSerializer


class TipOfficerReviewView(APIView):
    """Officer reviews tip -> forwards to detective."""
    permission_classes = [IsAuthenticated, IsPoliceOfficer]

    @transaction.atomic
    def post(self, request, pk):
        tip = get_object_or_404(Tip, pk=pk)
        if tip.status != Tip.STATUS_PENDING:
            return Response(
                {'success': False, 'error': {'message': 'Tip not pending.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        tip.status = Tip.STATUS_OFFICER_REVIEWED
        tip.reviewed_by_officer = request.user
        tip.save(update_fields=['status', 'reviewed_by_officer', 'updated_at'])
        
        # Send notifications to all detectives
        detectives = User.objects.filter(roles__name='Detective')
        for u in detectives:
            notify(u, 'Tip to confirm', tip.title, 'tip_pending_detective', 'Tip', tip.pk)
            
        log_audit(request.user, 'update', 'Tip', tip.pk, 'Officer reviewed')
        return Response({'success': True, 'data': TipListSerializer(tip).data})


class TipDetectiveConfirmView(APIView):
    """Detective confirms -> user gets unique reward code (create Reward)."""
    permission_classes = [IsAuthenticated, IsDetective]

    @transaction.atomic
    def post(self, request, pk):
        tip = get_object_or_404(Tip, pk=pk)
        if tip.status != Tip.STATUS_OFFICER_REVIEWED:
            return Response(
                {'success': False, 'error': {'message': 'Tip not in officer-reviewed state.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        try:
            amount = int(request.data.get('amount_rials', 0))
        except (ValueError, TypeError):
            amount = 0

        tip.status = Tip.STATUS_DETECTIVE_CONFIRMED
        tip.reviewed_by_detective = request.user
        tip.save(update_fields=['status', 'reviewed_by_detective', 'updated_at'])
        
        reward = Reward.objects.create(
            tip=tip,
            amount_rials=amount,
            recipient_national_id=tip.submitter.national_id or '',
        )
        
        notify(tip.submitter, 'Tip confirmed - Reward code', f'Code: {reward.unique_code}', 'reward_created', 'Reward', reward.pk)
        log_audit(request.user, 'approve', 'Tip', tip.pk, 'Detective confirmed; reward created')
        
        return Response({
            'success': True,
            'data': {
                'tip': TipListSerializer(tip).data,
                'reward_code': reward.unique_code,
                'amount_rials': reward.amount_rials,
            },
        })


class RewardLookupView(APIView):
    """Police view reward info using national_id + code."""
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]

    def post(self, request):
        ser = RewardClaimLookupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        
        reward = Reward.objects.filter(
            recipient_national_id=ser.validated_data['national_id'],
            unique_code=ser.validated_data['code'],
        ).first()
        
        if not reward:
            return Response(
                {'success': False, 'error': {'message': 'No reward found for this national ID and code.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        return Response({'success': True, 'data': RewardSerializer(reward).data})



















# """
# Tips: citizen submit; officer reviews -> detective confirms -> reward code.
# Reward lookup by national_id + code (police).
# """
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from django.shortcuts import get_object_or_404
# from django.contrib.auth import get_user_model

# from .models import Tip, Reward
# from .serializers import TipListSerializer, TipCreateSerializer, RewardSerializer, RewardClaimLookupSerializer
# from accounts.permissions import IsPoliceOfficer, IsDetective, IsOfficerOrAbove, has_any_role
# from core.utils import log_audit, notify

# User = get_user_model()


# class TipListCreateView(generics.ListCreateAPIView):
#     """List tips (filtered by role); citizen submits tip."""
#     permission_classes = [IsAuthenticated]
#     serializer_class = TipListSerializer

#     def get_queryset(self):
#         user = self.request.user
#         if not has_any_role(user, ['Police Officer', 'Detective', 'Sergeant', 'Captain', 'Police Chief', 'System Administrator']):
#             return Tip.objects.filter(submitter=user).order_by('-created_at')
#         return Tip.objects.all().order_by('-created_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return TipCreateSerializer
#         return TipListSerializer


# class TipOfficerReviewView(APIView):
#     """Officer reviews tip -> forwards to detective."""
#     permission_classes = [IsAuthenticated, IsPoliceOfficer]

#     def post(self, request, pk):
#         tip = get_object_or_404(Tip, pk=pk)
#         if tip.status != Tip.STATUS_PENDING:
#             return Response(
#                 {'success': False, 'error': {'message': 'Tip not pending.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         tip.status = Tip.STATUS_OFFICER_REVIEWED
#         tip.reviewed_by_officer = request.user
#         tip.save()
#         for u in User.objects.filter(roles__name='Detective'):
#             notify(u, 'Tip to confirm', tip.title, 'tip_pending_detective', 'Tip', tip.pk)
#         log_audit(request.user, 'update', 'Tip', tip.pk, 'Officer reviewed')
#         return Response({'success': True, 'data': TipListSerializer(tip).data})


# class TipDetectiveConfirmView(APIView):
#     """Detective confirms -> user gets unique reward code (create Reward)."""
#     permission_classes = [IsAuthenticated, IsDetective]

#     def post(self, request, pk):
#         tip = get_object_or_404(Tip, pk=pk)
#         if tip.status != Tip.STATUS_OFFICER_REVIEWED:
#             return Response(
#                 {'success': False, 'error': {'message': 'Tip not in officer-reviewed state.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         tip.status = Tip.STATUS_DETECTIVE_CONFIRMED
#         tip.reviewed_by_detective = request.user
#         tip.save()
#         amount = request.data.get('amount_rials', 0) or 0
#         reward = Reward.objects.create(
#             tip=tip,
#             amount_rials=amount,
#             recipient_national_id=tip.submitter.national_id or '',
#         )
#         notify(tip.submitter, 'Tip confirmed - Reward code', f'Code: {reward.unique_code}', 'reward_created', 'Reward', reward.pk)
#         log_audit(request.user, 'approve', 'Tip', tip.pk, 'Detective confirmed; reward created')
#         return Response({
#             'success': True,
#             'data': {
#                 'tip': TipListSerializer(tip).data,
#                 'reward_code': reward.unique_code,
#                 'amount_rials': reward.amount_rials,
#             },
#         })


# class RewardLookupView(APIView):
#     """Police view reward info using national_id + code."""
#     permission_classes = [IsAuthenticated, IsOfficerOrAbove]

#     def post(self, request):
#         ser = RewardClaimLookupSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         reward = Reward.objects.filter(
#             recipient_national_id=ser.validated_data['national_id'],
#             unique_code=ser.validated_data['code'],
#         ).first()
#         if not reward:
#             return Response(
#                 {'success': False, 'error': {'message': 'No reward found for this national ID and code.'}},
#                 status=status.HTTP_404_NOT_FOUND,
#             )
#         return Response({'success': True, 'data': RewardSerializer(reward).data})
