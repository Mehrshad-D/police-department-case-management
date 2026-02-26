"""
Tips: citizen submit; officer reviews -> detective confirms -> reward code.
Reward lookup by national_id + code (police).
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Tip, Reward, RewardPayment
from .serializers import TipListSerializer, TipCreateSerializer, RewardSerializer, RewardClaimLookupSerializer
from accounts.permissions import IsPoliceOfficer, IsDetective, IsOfficerOrAbove, has_any_role
from core.utils import log_audit, notify

User = get_user_model()


class TipListCreateView(generics.ListCreateAPIView):
    """List tips (filtered by role); citizen submits tip."""
    permission_classes = [IsAuthenticated]
    serializer_class = TipListSerializer

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
    """Officer reviews tip: if valid -> forward to detective; if invalid -> reject (user notified)."""
    permission_classes = [IsAuthenticated, IsPoliceOfficer]

    def post(self, request, pk):
        tip = get_object_or_404(Tip, pk=pk)
        if tip.status != Tip.STATUS_PENDING:
            return Response(
                {'success': False, 'error': {'message': 'Tip not pending.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        action = request.data.get('action', 'approve')  # 'approve' | 'reject'
        if action == 'reject':
            tip.status = Tip.STATUS_REJECTED
            tip.reviewed_by_officer = request.user
            tip.save()
            notify(tip.submitter, 'Tip rejected', request.data.get('message', 'Your tip was rejected as invalid.'), 'tip_rejected', 'Tip', tip.pk)
            log_audit(request.user, 'reject', 'Tip', tip.pk, 'Tip rejected by officer')
            return Response({'success': True, 'data': TipListSerializer(tip).data, 'message': 'Tip rejected.'})
        tip.status = Tip.STATUS_OFFICER_REVIEWED
        tip.reviewed_by_officer = request.user
        tip.save()
        for u in User.objects.filter(roles__name='Detective'):
            notify(u, 'Tip to confirm', tip.title, 'tip_pending_detective', 'Tip', tip.pk)
        log_audit(request.user, 'update', 'Tip', tip.pk, 'Officer reviewed; sent to detective')
        return Response({'success': True, 'data': TipListSerializer(tip).data})


class TipDetectiveConfirmView(APIView):
    """Detective confirms -> user gets unique reward code (create Reward)."""
    permission_classes = [IsAuthenticated, IsDetective]

    def post(self, request, pk):
        tip = get_object_or_404(Tip, pk=pk)
        if tip.status != Tip.STATUS_OFFICER_REVIEWED:
            return Response(
                {'success': False, 'error': {'message': 'Tip not in officer-reviewed state.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tip.status = Tip.STATUS_DETECTIVE_CONFIRMED
        tip.reviewed_by_detective = request.user
        tip.save()
        amount = request.data.get('amount_rials', 0) or 0
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


class RewardRedeemView(APIView):
    """Police marks reward as claimed when user redeems at police office (national_id + code)."""
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
        if reward.claimed:
            return Response(
                {'success': False, 'error': {'message': 'Reward already redeemed.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.utils import timezone
        reward.claimed = True
        reward.claimed_at = timezone.now()
        reward.save(update_fields=['claimed', 'claimed_at'])
        RewardPayment.objects.create(
            reward=reward,
            officer=request.user,
            amount_rials=reward.amount_rials,
        )
        log_audit(request.user, 'update', 'Reward', reward.pk, 'Reward redeemed at police office')
        return Response({'success': True, 'data': RewardSerializer(reward).data, 'message': 'Reward redeemed.'})


class RewardVerifyView(APIView):
    """POST /api/rewards/verify — Police: verify reward by national_id + code. Returns user info, amount, case/suspect info, payment status."""
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]

    def post(self, request):
        ser = RewardClaimLookupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reward = Reward.objects.select_related('tip', 'tip__submitter', 'tip__case', 'suspect', 'suspect__case').filter(
            recipient_national_id=ser.validated_data['national_id'],
            unique_code=ser.validated_data['code'],
        ).first()
        if not reward:
            return Response(
                {'success': False, 'error': {'message': 'No reward found for this national ID and code.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        user_info = None
        case_info = None
        suspect_info = None
        if reward.tip_id:
            user_info = {
                'id': reward.tip.submitter_id,
                'username': reward.tip.submitter.username,
                'full_name': reward.tip.submitter.full_name,
                'national_id': reward.tip.submitter.national_id,
            }
            if reward.tip.case_id:
                case_info = {'id': reward.tip.case_id, 'title': reward.tip.case.title}
            if reward.tip.suspect_id:
                suspect_info = {'id': reward.tip.suspect_id, 'case_id': reward.tip.suspect.case_id}
        if reward.suspect_id and not suspect_info:
            suspect_info = {'id': reward.suspect_id, 'case_id': reward.suspect.case_id}
        payment_status = 'paid' if reward.claimed else 'unpaid'
        payments = list(reward.payments.values('id', 'amount_rials', 'paid_at', 'officer_id').order_by('-paid_at')[:1])
        return Response({
            'success': True,
            'data': {
                'reward': RewardSerializer(reward).data,
                'user_info': user_info,
                'reward_amount': reward.amount_rials,
                'case_info': case_info,
                'suspect_info': suspect_info,
                'payment_status': payment_status,
                'payment_record': payments[0] if payments else None,
            },
        })
