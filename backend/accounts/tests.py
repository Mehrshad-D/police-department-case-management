from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Role

User = get_user_model()

class AccountsTestCase(TestCase):
    def setUp(self):
        """ایجاد داده‌های اولیه برای تست"""
        self.client = APIClient()
        
        # ایجاد نقش‌های مورد نیاز
        self.admin_role = Role.objects.create(name='System Administrator')
        self.officer_role = Role.objects.create(name='Police Officer')
        self.detective_role = Role.objects.create(name='Detective')
        
        # ایجاد کاربران تست
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            phone='09121111111',
            national_id='0012345678',
            full_name='مدیر سیستم',
            password='Admin@123456'
        )
        self.admin_user.roles.add(self.admin_role)
        
        self.normal_user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            phone='09122222222',
            national_id='0012345679',
            full_name='کاربر عادی',
            password='User@123456'
        )

    # تست ۱: ثبت‌نام کاربر جدید با اطلاعات معتبر
    def test_user_registration_success(self):
        """کاربر جدید با اطلاعات کامل و معتبر ثبت‌نام می‌کند"""
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'password': 'NewUser@123456',
            'email': 'newuser@test.com',
            'phone': '09123333333',
            'full_name': 'کاربر جدید',
            'national_id': '0012345680'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'newuser')
        
        # بررسی اینکه کاربر واقعاً در دیتابیس ایجاد شده
        self.assertTrue(User.objects.filter(username='newuser').exists())

    # تست ۲: ثبت‌نام با نام کاربری تکراری
    def test_user_registration_duplicate_username(self):
        """ثبت‌نام با نام کاربری تکراری باید خطا بدهد"""
        response = self.client.post('/api/auth/register/', {
            'username': 'admin',  # این نام کاربری قبلاً وجود دارد
            'password': 'NewUser@123456',
            'email': 'newemail@test.com',
            'phone': '09123333333',
            'full_name': 'کاربر جدید',
            'national_id': '0012345680'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('username', response.data['error']['message'])

    # تست ۳: ورود با شناسه و رمز صحیح
    def test_login_with_valid_credentials(self):
        """کاربر می‌تواند با نام کاربری و رمز صحیح وارد شود"""
        response = self.client.post('/api/auth/login/', {
            'identifier': 'admin',
            'password': 'Admin@123456'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access', response.data['data']['tokens'])

    # تست ۴: ورود با کد ملی به جای نام کاربری
    def test_login_with_national_id(self):
        """کاربر می‌تواند با کد ملی وارد شود (ویژگی چند-شناسه)"""
        response = self.client.post('/api/auth/login/', {
            'identifier': '0012345678',  # کد ملی ادمین
            'password': 'Admin@123456'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['username'], 'admin')

    # تست ۵: دسترسی غیرمجاز به پنل ادمین
    def test_admin_panel_access_denied_for_normal_user(self):
        """کاربر عادی نباید به پنل ادمین دسترسی داشته باشد"""
        # ورود با کاربر عادی
        self.client.force_authenticate(user=self.normal_user)
        
        response = self.client.get('/api/auth/users/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)