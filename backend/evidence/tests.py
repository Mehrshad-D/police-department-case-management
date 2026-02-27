from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Role
from cases.models import Case
from evidence.models import Evidence, BiologicalEvidence, BiologicalEvidenceImage

User = get_user_model()

class EvidenceTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # ایجاد نقش‌ها
        self.officer_role = Role.objects.create(name='Police Officer')
        self.detective_role = Role.objects.create(name='Detective')
        self.forensic_role = Role.objects.create(name='Forensic Doctor')
        
        # ایجاد کاربران
        self.officer = User.objects.create_user(
            username='officer',
            password='Officer@123456',
            email='officer@test.com',
            phone='09121111111',
            national_id='0012345678',
            full_name='افسر'
        )
        self.officer.roles.add(self.officer_role)
        
        self.forensic = User.objects.create_user(
            username='forensic',
            password='Forensic@123456',
            email='forensic@test.com',
            phone='09122222222',
            national_id='0012345679',
            full_name='پزشک قانونی'
        )
        self.forensic.roles.add(self.forensic_role)
        
        # ایجاد یک پرونده تست
        self.case = Case.objects.create(
            title='پرونده تست',
            description='توضیحات پرونده',
            created_by=self.officer
        )


    # تست ۲: آپلود مدرک زیستی بدون تصویر (خطا)
    def test_upload_biological_evidence_without_image_fails(self):
        """آپلود مدرک زیستی بدون تصویر باید خطا بدهد"""
        self.client.force_authenticate(user=self.officer)
        
        response = self.client.post('/api/evidence/', {
            'case': self.case.id,
            'evidence_type': 'biological',
            'title': 'نمونه خون',
            'description': 'بدون تصویر'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('images', response.data['error']['message'])

    # تست ۳: تأیید مدرک زیستی توسط پزشک قانونی
    def test_biological_evidence_review_by_forensic(self):
        """پزشک قانونی می‌تواند مدرک زیستی را تأیید کند"""
        # ابتدا یک مدرک زیستی ایجاد می‌کنیم
        evidence = Evidence.objects.create(
            case=self.case,
            evidence_type='biological',
            title='نمونه خون',
            description='نمونه تست',
            recorder=self.officer
        )
        biological = BiologicalEvidence.objects.create(evidence=evidence)
        
        self.client.force_authenticate(user=self.forensic)
        
        response = self.client.post(f'/api/evidence/{evidence.id}/biological-review/', {
            'verification_status': 'verified_forensic',
            'verification_result': 'نمونه با DNA مظنون مطابقت دارد'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        biological.refresh_from_db()
        self.assertEqual(biological.verification_status, 'verified_forensic')
        self.assertEqual(biological.reviewed_by, self.forensic)

    # تست ۴: ایجاد لینک بین دو مدرک در تخته کارآگاه
    def test_create_evidence_link(self):
        """کارآگاه می‌تواند دو مدرک را در تخته کارآگاه به هم وصل کند"""
        evidence1 = Evidence.objects.create(
            case=self.case,
            evidence_type='witness',
            title='شاهد ۱',
            recorder=self.officer
        )
        evidence2 = Evidence.objects.create(
            case=self.case,
            evidence_type='vehicle',
            title='ماشین مشکوک',
            recorder=self.officer
        )
        
        self.client.force_authenticate(user=self.officer)
        
        response = self.client.post(f'/api/cases/{self.case.id}/evidence-links/', {
            'evidence_from': evidence1.id,
            'evidence_to': evidence2.id,
            'link_type': 'red'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['evidence_from'], evidence1.id)
        self.assertEqual(response.data['evidence_to'], evidence2.id)

    # تست ۵: آپلود فایل با حجم بیش از حد مجاز
    def test_upload_file_exceeding_size_limit(self):
        """آپلود فایل با حجم بیش از ۱۰ مگابایت باید خطا بدهد"""
        self.client.force_authenticate(user=self.officer)
        
        # ایجاد فایل ۱۱ مگابایتی
        large_file = SimpleUploadedFile(
            "large_file.jpg",
            b"x" * (11 * 1024 * 1024),  # 11 مگابایت
            content_type="image/jpeg"
        )
        
        response = self.client.post('/api/evidence/', {
            'case': self.case.id,
            'evidence_type': 'witness',
            'title': 'فایل حجیم',
            'media_file': large_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('size', response.data['error']['message'].lower())