"""
Create default roles from spec. Admin can add/remove/modify later via API or admin.
"""
from django.core.management.base import BaseCommand
from accounts.models import Role

DEFAULT_ROLES = [
    'System Administrator',
    'Police Chief',
    'Captain',
    'Sergeant',
    'Detective',
    'Police Officer',
    'Intern',
    'Complainant / Witness',
    'Suspect / Criminal',
    'Judge',
    'Forensic Doctor',
    'Basic User',
]


class Command(BaseCommand):
    help = 'Create default user roles'

    def handle(self, *args, **options):
        created = 0
        for name in DEFAULT_ROLES:
            _, created_this = Role.objects.get_or_create(name=name, defaults={'description': name})
            if created_this:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Roles ready. Created {created} new roles.'))
