from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Role
from cases.models import Case, Complaint

User = get_user_model()

class CasesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # ایجاد نقش‌ها
        self.intern_role = Role.objects.create(name='Intern')
        self.officer_role = Role.objects.create(name='Police Officer')
        self.detective_role = Role.objects.create(name='Detective')
        self.complainant_role = Role.objects.create(name='Complainant / Witness')
        
        # ایجاد کاربران
        self.intern = User.objects.create_user(
            username='intern',
            password='Intern@123456',
            email='intern@test.com',
            phone='09121111111',
            national_id='0012345678',
            full_name='کارآموز'
        )
        self.intern.roles.add(self.intern_role)
        
        self.officer = User.objects.create_user(
            username='officer',
            password='Officer@123456',
            email='officer@test.com',
            phone='09122222222',
            national_id='0012345679',
            full_name='افسر'
        )
        self.officer.roles.add(self.officer_role)
        
        self.complainant = User.objects.create_user(
            username='complainant',
            password='Complainant@123456',
            email='complainant@test.com',
            phone='09123333333',
            national_id='0012345680',
            full_name='شاکی'
        )
        self.complainant.roles.add(self.complainant_role)

    # تست ۲: بررسی شکایت توسط کارآموز (تأیید و ارجاع به افسر)
    def test_complaint_review_by_intern_approve(self):
        """کارآموز شکایت را تأیید کرده و به افسر ارجاع می‌دهد"""
        # ابتدا یک شکایت ایجاد می‌کنیم
        complaint = Complaint.objects.create(
            complainant=self.complainant,
            title='سرقت از منزل',
            description='توضیحات کامل',
            status='pending_trainee'
        )
        
        # کارآموز وارد می‌شود
        self.client.force_authenticate(user=self.intern)
        
        response = self.client.post(f'/api/complaints/{complaint.id}/trainee-review/', {
            'action': 'approve'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'pending_officer')
        self.assertEqual(complaint.reviewed_by_trainee, self.intern)

    # تست ۳: بررسی شکایت توسط کارآموز (برگشت برای اصلاح)
    def test_complaint_review_by_intern_return_for_correction(self):
        """کارآموز شکایت را برای اصلاح برمی‌گرداند"""
        complaint = Complaint.objects.create(
            complainant=self.complainant,
            title='سرقت از منزل',
            description='توضیحات ناقص',
            status='pending_trainee'
        )
        
        self.client.force_authenticate(user=self.intern)
        
        response = self.client.post(f'/api/complaints/{complaint.id}/trainee-review/', {
            'action': 'return_correction',
            'correction_message': 'لطفاً تاریخ دقیق را وارد کنید'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'correction_needed')
        self.assertEqual(complaint.last_correction_message, 'لطفاً تاریخ دقیق را وارد کنید')

    # تست ۴: تأیید نهایی توسط افسر و ایجاد پرونده
    def test_officer_approval_and_case_creation(self):
        """افسر شکایت را تأیید کرده و پرونده جدید ایجاد می‌شود"""
        complaint = Complaint.objects.create(
            complainant=self.complainant,
            title='سرقت از منزل',
            description='توضیحات کامل',
            status='pending_officer'
        )
        
        self.client.force_authenticate(user=self.officer)
        
        response = self.client.post(f'/api/complaints/{complaint.id}/officer-review/', {
            'action': 'approve'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'approved')
        self.assertIsNotNone(complaint.case)
        self.assertEqual(complaint.case.title, complaint.title)

    # تست ۵: مکانیزم رد خودکار پس از سه بار اصلاح
    def test_auto_rejection_after_three_corrections(self):
        """شکایت پس از سه بار اصلاح ناموفق، خودکار رد می‌شود"""
        complaint = Complaint.objects.create(
            complainant=self.complainant,
            title='سرقت از منزل',
            description='توضیحات ناقص',
            status='correction_needed',
            correction_count=2  # دو بار قبلاً اصلاح شده
        )
        
        self.client.force_authenticate(user=self.complainant)
        
        # شاکی برای سومین بار اصلاح می‌فرستد
        response = self.client.post(f'/api/complaints/{complaint.id}/correct/', {
            'description': 'هنوز توضیحات ناقص است'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'rejected')
        self.assertEqual(complaint.correction_count, 3)