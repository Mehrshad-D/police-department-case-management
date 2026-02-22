"""
Assign the "System Administrator" role to all superusers.
Run this after createsuperuser so your admin account can use the app's Admin Panel.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign System Administrator role to all superusers (for custom Admin Panel access)'

    def handle(self, *args, **options):
        role, _ = Role.objects.get_or_create(
            name='System Administrator',
            defaults={'description': 'System Administrator'},
        )
        superusers = User.objects.filter(is_superuser=True)
        count = 0
        for user in superusers:
            if not user.roles.filter(pk=role.pk).exists():
                user.roles.add(role)
                count += 1
                self.stdout.write(f'  Assigned to: {user.username}')
        self.stdout.write(self.style.SUCCESS(f'Done. Assigned System Administrator to {count} user(s).'))
        if count == 0 and superusers.exists():
            self.stdout.write(self.style.NOTICE('All superusers already had the role.'))
