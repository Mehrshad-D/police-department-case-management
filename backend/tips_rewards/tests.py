from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Role
from cases.models import Case
from tips_rewards.models import Tip, Reward

User = get_user_model()


class TipRewardTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="citizen",
            email="citizen@test.com",
            password="pass"
        )

        self.case = Case.objects.create(
            title="Case",
            description="desc",
            severity=Case.SEVERITY_LEVEL_3,
            status=Case.STATUS_OPEN,
            is_crime_scene_case=False,
            created_by=self.user
        )

    def test_tip_creation(self):
        tip = Tip.objects.create(
            submitter=self.user,
            case=self.case,
            title="Info",
            description="Important info"
        )

        self.assertEqual(tip.status, Tip.STATUS_PENDING)

    def test_reward_creation(self):
        reward = Reward.objects.create(
            amount_rials=20000000,
            recipient_national_id="1234567890"
        )

        self.assertTrue(reward.unique_code)