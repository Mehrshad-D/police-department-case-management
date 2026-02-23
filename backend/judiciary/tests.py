from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import Role
from cases.models import Case
from judiciary.models import Trial

User = get_user_model()


class JudiciaryTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.judge_role = Role.objects.create(name="Police Chief")

        self.judge = User.objects.create_user(
            username="judge",
            email="judge@test.com",
            password="pass"
        )
        self.judge.roles.add(self.judge_role)

        self.case = Case.objects.create(
            title="Test Case",
            description="desc",
            severity=Case.SEVERITY_LEVEL_3,
            status=Case.STATUS_OPEN,
            is_crime_scene_case=False,
            created_by=self.judge
        )

    def test_create_trial(self):
        self.client.force_authenticate(self.judge)

        url = reverse("trial-list-create")
        response = self.client.post(url, {
            "case": self.case.id,
            "judge": self.judge.id
        })

        self.assertIn(response.status_code, [200, 201])
        self.assertEqual(Trial.objects.count(), 1)