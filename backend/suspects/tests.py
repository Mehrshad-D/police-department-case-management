from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Role
from cases.models import Case
from suspects.models import Suspect, CaptainDecision

User = get_user_model()

class SuspectsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # ایجاد نقش‌ها
        self.detective_role = Role.objects.create(name='Detective')
        self.sergeant_role = Role.objects.create(name='Sergeant')
        self.captain_role = Role.objects.create(name='Captain')
        
        # ایجاد کاربران
        self.detective = User.objects.create_user(
            username='detective',
            password='Detective@123456',
            email='detective@test.com',
            phone='09121111111',
            national_id='0012345678',
            full_name='کارآگاه'
        )
        self.detective.roles.add(self.detective_role)
        
        self.sergeant = User.objects.create_user(
            username='sergeant',
            password='Sergeant@123456',
            email='sergeant@test.com',
            phone='09122222222',
            national_id='0012345679',
            full_name='سرجوخه'
        )
        self.sergeant.roles.add(self.sergeant_role)
        
        self.captain = User.objects.create_user(
            username='captain',
            password='Captain@123456',
            email='captain@test.com',
            phone='09123333333',
            national_id='0012345680',
            full_name='کاپیتان'
        )
        self.captain.roles.add(self.captain_role)
        
        # ایجاد مظنون
        self.suspect_user = User.objects.create_user(
            username='suspect',
            password='Suspect@123456',
            email='suspect@test.com',
            phone='09124444444',
            national_id='0012345681',
            full_name='مظنون'
        )
        
        # ایجاد پرونده
        self.case = Case.objects.create(
            title='پرونده قتل',
            description='قتل در خیابان',
            severity=Case.SEVERITY_LEVEL_1,  # درجه ۳ (مهم)
            created_by=self.detective,
            assigned_detective=self.detective
        )

    # تست ۱: پیشنهاد مظنون توسط کارآگاه
    def test_detective_proposes_suspect(self):
        """کارآگاه یک کاربر را به عنوان مظنون پیشنهاد می‌دهد"""
        self.client.force_authenticate(user=self.detective)
        
        response = self.client.post('/api/suspects/', {
            'case_id': self.case.id,
            'user_id': self.suspect_user.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['status'], 'under_investigation')
        self.assertEqual(response.data['data']['proposed_by_detective'], self.detective.id)
        
        # بررسی اینکه مظنون در دیتابیس ایجاد شده
        self.assertTrue(Suspect.objects.filter(case=self.case, user=self.suspect_user).exists())

    # تست ۲: تأیید مظنون توسط سرجوخه (بازداشت)
    def test_sergeant_approves_suspect(self):
        """سرجوخه مظنون را تأیید کرده و دستور بازداشت صادر می‌شود"""
        suspect = Suspect.objects.create(
            case=self.case,
            user=self.suspect_user,
            proposed_by_detective=self.detective,
            status='under_investigation'
        )
        
        self.client.force_authenticate(user=self.sergeant)
        
        response = self.client.post(f'/api/suspects/{suspect.id}/supervisor-review/', {
            'action': 'approve'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suspect.refresh_from_db()
        self.assertEqual(suspect.status, 'arrested')
        self.assertEqual(suspect.approved_by_supervisor, self.sergeant)

    # تست ۳: رد مظنون توسط سرجوخه
    def test_sergeant_rejects_suspect(self):
        """سرجوخه پیشنهاد مظنون را رد می‌کند"""
        suspect = Suspect.objects.create(
            case=self.case,
            user=self.suspect_user,
            proposed_by_detective=self.detective,
            status='under_investigation'
        )
        
        self.client.force_authenticate(user=self.sergeant)
        
        response = self.client.post(f'/api/suspects/{suspect.id}/supervisor-review/', {
            'action': 'reject',
            'rejection_message': 'ادله کافی برای بازداشت وجود ندارد'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suspect.refresh_from_db()
        self.assertEqual(suspect.status, 'rejected')
        self.assertEqual(suspect.rejection_message, 'ادله کافی برای بازداشت وجود ندارد')

    # تست ۴: محاسبه خودکار Most Wanted پس از ۳۰ روز
    def test_most_wanted_after_thirty_days(self):
        """مظنون پس از ۳۰ روز تحت تعقیب به Most Wanted تبدیل می‌شود"""
        # ایجاد مظنون با تاریخ ۳۱ روز قبل
        suspect = Suspect.objects.create(
            case=self.case,
            user=self.suspect_user,
            proposed_by_detective=self.detective,
            approved_by_supervisor=self.sergeant,
            approved_at=timezone.now(),
            status='under_investigation'
        )
        
        # تنظیم first_pursuit_date به ۳۱ روز قبل
        suspect.first_pursuit_date = timezone.now() - timedelta(days=31)
        suspect.save()
        
        # فراخوانی متد به‌روزرسانی
        suspect.update_most_wanted()
        suspect.refresh_from_db()
        
        self.assertEqual(suspect.status, 'most_wanted')
        
        # محاسبه امتیاز و جایزه
        days = suspect.days_under_investigation
        degree = suspect.crime_degree()  # برای قتل درجه ۴ = 1-4? درجه جرم: سطح ۱ (مهم) = ۳
        # سطح ۱ (مهم) => درجه ۳
        self.assertGreater(days, 30)
        self.assertEqual(suspect.ranking_score(), days * degree)
        self.assertEqual(suspect.reward_rials(), suspect.ranking_score() * 20000000)

    # تست ۵: تصمیم کاپیتان برای جرایم بحرانی نیاز به تأیید رئیس دارد
    def test_captain_decision_crisis_case_needs_chief_approval(self):
        """در جرایم بحرانی، تصمیم کاپیتان نیاز به تأیید رئیس پلیس دارد"""
        # ایجاد پرونده بحرانی
        crisis_case = Case.objects.create(
            title='قتل سریالی',
            description='چندین قتل',
            severity=Case.SEVERITY_CRISIS,  # بحرانی
            created_by=self.detective
        )
        
        suspect = Suspect.objects.create(
            case=crisis_case,
            user=self.suspect_user,
            proposed_by_detective=self.detective,
            approved_by_supervisor=self.sergeant,
            status='arrested'
        )
        
        self.client.force_authenticate(user=self.captain)
        
        response = self.client.post('/api/captain-decisions/', {
            'suspect_id': suspect.id,
            'case_id': crisis_case.id,
            'final_decision': 'guilty',
            'reasoning': 'ادله کافی است'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['requires_chief_approval'])
        
        # بررسی اینکه هنوز وضعیت تغییر نکرده
        suspect.refresh_from_db()
        self.assertEqual(suspect.status, 'arrested')
