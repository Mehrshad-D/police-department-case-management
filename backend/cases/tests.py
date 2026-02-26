from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import Role
from cases.models import Case

User = get_user_model()


class CaseFlowTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        # IMPORTANT: Role name must match permission exactly
        self.officer_role = Role.objects.create(name="Police Officer")

        self.officer = User.objects.create_user(
            username="officer1",
            email="officer1@test.com",
            password="pass"
        )
        self.officer.roles.add(self.officer_role)

    def test_create_case(self):
        self.client.force_authenticate(self.officer)

        url = reverse("case-list-create")

        response = self.client.post(url, {
            "title": "Robbery",
            "description": "Bank robbery",
            "severity": Case.SEVERITY_LEVEL_3,
            "status": Case.STATUS_OPEN,
            "is_crime_scene_case": False
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Case.objects.count(), 1)