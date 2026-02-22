"""
Helpers for audit trail and notifications.
"""
from core.models import AuditLog, Notification


def log_audit(user, action, model_name='', object_id='', description='', extra_data=None):
    """Create an audit log entry."""
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        description=description,
        extra_data=extra_data or {},
    )


def notify(recipient, title, message='', notification_type='', related_model='', related_id=''):
    """Create a notification for a user."""
    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        related_model=related_model,
        related_id=str(related_id),
    )
