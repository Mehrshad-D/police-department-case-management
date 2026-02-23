from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Role
from cases.models import Case
from suspects.models import Suspect
from judiciary.models import Trial
from payments.models import BailPayment, FinePayment

User = get_user_model()


class PaymentsTest(TestCase):

    def setUp(self):
        self.supervisor_role = Role.objects.create(name="Sergeant")

        self.supervisor = User.objects.create_user(
            username="sergeant",
            email="sergeant@test.com",
            password="pass"
        )
        self.supervisor.roles.add(self.supervisor_role)

        self.case = Case.objects.create(
            title="Case",
            description="desc",
            severity=Case.SEVERITY_LEVEL_3,
            status=Case.STATUS_OPEN,
            is_crime_scene_case=False,
            created_by=self.supervisor
        )

        self.suspect = Suspect.objects.create(
            case=self.case,
            user=self.supervisor
        )

        self.trial = Trial.objects.create(
            case=self.case,
            judge=self.supervisor
        )

    def test_bail_payment_creation(self):
        bail = BailPayment.objects.create(
            suspect=self.suspect,
            amount_rials=1000000
        )

        self.assertEqual(bail.status, BailPayment.STATUS_PENDING)

    def test_fine_payment_creation(self):
        fine = FinePayment.objects.create(
            trial=self.trial,
            payer=self.supervisor,
            amount_rials=500000
        )

        self.assertEqual(fine.status, FinePayment.STATUS_PENDING)