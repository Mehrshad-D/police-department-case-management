from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Role
from cases.models import Case
from tips_rewards.models import Tip, Reward

User = get_user_model()

class TipsRewardsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # ایجاد نقش‌ها
        self.citizen_role = Role.objects.create(name='Complainant / Witness')
        self.officer_role = Role.objects.create(name='Police Officer')
        self.detective_role = Role.objects.create(name='Detective')
        
        # ایجاد کاربران
        self.citizen = User.objects.create_user(
            username='citizen',
            password='Citizen@123456',
            email='citizen@test.com',
            phone='09121111111',
            national_id='0012345678',
            full_name='شهروند'
        )
        self.citizen.roles.add(self.citizen_role)
        
        self.officer = User.objects.create_user(
            username='officer',
            password='Officer@123456',
            email='officer@test.com',
            phone='09122222222',
            national_id='0012345679',
            full_name='افسر'
        )
        self.officer.roles.add(self.officer_role)
        
        self.detective = User.objects.create_user(
            username='detective',
            password='Detective@123456',
            email='detective@test.com',
            phone='09123333333',
            national_id='0012345680',
            full_name='کارآگاه'
        )
        self.detective.roles.add(self.detective_role)
        
        # ایجاد پرونده
        self.case = Case.objects.create(
            title='پرونده سرقت',
            description='سرقت از بانک',
            created_by=self.officer
        )

    # تست ۲: افسر نکته را بررسی و به کارآگاه ارجاع می‌دهد
    def test_officer_reviews_and_forwards_tip(self):
        """افسر نکته را بررسی کرده و برای تأیید به کارآگاه ارجاع می‌دهد"""
        tip = Tip.objects.create(
            submitter=self.citizen,
            case=self.case,
            title='ماشین مشکوک',
            description='پراید سفید',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.officer)
        
        response = self.client.post(f'/api/tips/{tip.id}/officer-review/', {
            'action': 'approve'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tip.refresh_from_db()
        self.assertEqual(tip.status, 'officer_reviewed')
        self.assertEqual(tip.reviewed_by_officer, self.officer)

    # تست ۳: کارآگاه نکته را تأیید کرده و کد جایزه صادر می‌کند
    def test_detective_confirms_tip_and_creates_reward(self):
        """کارآگاه نکته را تأیید کرده و کد جایزه یکتا صادر می‌کند"""
        tip = Tip.objects.create(
            submitter=self.citizen,
            case=self.case,
            title='ماشین مشکوک',
            description='پراید سفید',
            status='officer_reviewed',
            reviewed_by_officer=self.officer
        )
        
        self.client.force_authenticate(user=self.detective)
        
        response = self.client.post(f'/api/tips/{tip.id}/detective-confirm/', {
            'amount_rials': 5000000  # ۵ میلیون تومان
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tip.refresh_from_db()
        self.assertEqual(tip.status, 'detective_confirmed')
        
        # بررسی اینکه جایزه ایجاد شده
        self.assertTrue(Reward.objects.filter(tip=tip).exists())
        reward = Reward.objects.get(tip=tip)
        self.assertEqual(reward.amount_rials, 5000000)
        self.assertEqual(reward.recipient_national_id, self.citizen.national_id)
        self.assertIsNotNone(reward.unique_code)  # کد یکتا باید تولید شده باشد
        self.assertFalse(reward.claimed)

    # تست ۴: جستجوی جایزه با کد ملی و کد یکتا
    def test_reward_lookup_with_national_id_and_code(self):
        """افسر می‌تواند جایزه را با کد ملی و کد یکتا جستجو کند"""
        tip = Tip.objects.create(
            submitter=self.citizen,
            case=self.case,
            title='ماشین مشکوک',
            description='پراید سفید',
            status='detective_confirmed',
            reviewed_by_officer=self.officer,
            reviewed_by_detective=self.detective
        )
        
        reward = Reward.objects.create(
            tip=tip,
            amount_rials=5000000,
            recipient_national_id=self.citizen.national_id,
            unique_code='TESTCODE123456'
        )
        
        self.client.force_authenticate(user=self.officer)
        
        response = self.client.post('/api/rewards/lookup/', {
            'national_id': self.citizen.national_id,
            'code': 'TESTCODE123456'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['amount_rials'], 5000000)
        self.assertFalse(response.data['data']['claimed'])

    # تست ۵: دریافت جایزه در کلانتری (Redeem)
    def test_reward_redeem_at_police_station(self):
        """شهروند با مراجعه به کلانتری جایزه خود را دریافت می‌کند"""
        tip = Tip.objects.create(
            submitter=self.citizen,
            case=self.case,
            title='ماشین مشکوک',
            description='پراید سفید',
            status='detective_confirmed'
        )
        
        reward = Reward.objects.create(
            tip=tip,
            amount_rials=5000000,
            recipient_national_id=self.citizen.national_id,
            unique_code='TESTCODE123456'
        )
        
        self.client.force_authenticate(user=self.officer)
        
        response = self.client.post('/api/rewards/redeem/', {
            'national_id': self.citizen.national_id,
            'code': 'TESTCODE123456'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reward.refresh_from_db()
        self.assertTrue(reward.claimed)
        self.assertIsNotNone(reward.claimed_at)
        
        # بررسی ایجاد رکورد پرداخت
        self.assertEqual(reward.payments.count(), 1)
        self.assertEqual(reward.payments.first().officer, self.officer)
        self.assertEqual(reward.payments.first().amount_rials, 5000000)