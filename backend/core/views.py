"""Notifications, audit log, and aggregated statistics."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework import serializers
from .models import Notification


class StatisticsView(APIView):
    """Aggregated statistics for dashboard/home. Public or authenticated."""
    permission_classes = [AllowAny]

    def get(self, request):
        from cases.models import Case, Complaint
        from evidence.models import Evidence
        from suspects.models import Suspect
        from accounts.models import User
        stats = {
            'cases_total': Case.objects.count(),
            'cases_open': Case.objects.filter(status=Case.STATUS_OPEN).count(),
            'complaints_total': Complaint.objects.count(),
            'complaints_pending': Complaint.objects.filter(
                status__in=(Complaint.STATUS_PENDING_TRAINEE, Complaint.STATUS_PENDING_OFFICER)
            ).count(),
            'evidence_total': Evidence.objects.count(),
            'suspects_total': Suspect.objects.count(),
            'suspects_high_priority': Suspect.objects.filter(status=Suspect.STATUS_MOST_WANTED).count(),
            'users_total': User.objects.count(),
        }
        return Response({'success': True, 'data': stats})


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'related_model', 'related_id', 'read', 'created_at']


class NotificationListView(generics.ListAPIView):
    """List current user's notifications."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


class NotificationMarkReadView(APIView):
    """Mark notification as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = Notification.objects.filter(recipient=request.user, pk=pk).first()
        if not notification:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)
        notification.read = True
        notification.save()
        return Response({'success': True})
