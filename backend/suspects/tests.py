from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from cases.models import Case
from suspects.models import Suspect, Interrogation
from accounts.models import Role

User = get_user_model()


class SuspectFlowTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Roles
        self.detective_role = Role.objects.create(name="Detective")
        self.sergeant_role = Role.objects.create(name="Sergeant")
        self.captain_role = Role.objects.create(name="Captain")
        self.chief_role = Role.objects.create(name="Police Chief")

        # Users
        self.detective = User.objects.create_user(
            username="detective",
            email="detective@test.com",
            password="pass"
        )
        self.detective.roles.add(self.detective_role)

        self.sergeant = User.objects.create_user(
            username="sergeant",
            email="sergeant@test.com",
            password="pass"
        )
        self.sergeant.roles.add(self.sergeant_role)

        self.captain = User.objects.create_user(
            username="captain",
            email="captain@test.com",
            password="pass"
        )
        self.captain.roles.add(self.captain_role)

        self.chief = User.objects.create_user(
            username="chief",
            email="chief@test.com",
            password="pass"
        )
        self.chief.roles.add(self.chief_role)

        self.suspect_user = User.objects.create_user(
            username="suspect_user",
            email="suspect@test.com",
            password="pass"
        )

        self.case = Case.objects.create(
            title="Robbery Case",
            description="Bank robbery",
            severity=2
        )

    def test_full_suspect_flow(self):

        # 1️⃣ Detective proposes suspect
        self.client.force_authenticate(self.detective)

        url = reverse("suspect-list-create")
        response = self.client.post(url, {
            "user_id": self.suspect_user.id,
            "case_id": self.case.id
        })
        self.assertEqual(response.status_code, 201)

        suspect = Suspect.objects.get(case=self.case)

        # 2️⃣ Sergeant approves
        self.client.force_authenticate(self.sergeant)

        url = reverse("suspect-supervisor-review", args=[suspect.id])
        response = self.client.post(url, {"action": "approve"})
        self.assertEqual(response.status_code, 200)

        # 3️⃣ Create interrogation
        self.client.force_authenticate(self.detective)

        url = reverse("interrogation-list-create")
        response = self.client.post(url, {
            "suspect": suspect.id,
            "detective_probability": 8,
            "supervisor_probability": 7
        })
        self.assertEqual(response.status_code, 201)

        interrogation = Interrogation.objects.first()

        # 4️⃣ Captain decision
        self.client.force_authenticate(self.captain)

        url = reverse("interrogation-captain-decision", args=[interrogation.id])
        response = self.client.post(url, {
            "captain_decision": "Strong evidence"
        })
        self.assertEqual(response.status_code, 200)

        # 5️⃣ Chief confirm
        self.client.force_authenticate(self.chief)

        url = reverse("interrogation-chief-confirm", args=[interrogation.id])
        response = self.client.post(url, {
            "final_decision": "approve"
        })
        self.assertEqual(response.status_code, 200)