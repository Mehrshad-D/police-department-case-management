from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Role

User = get_user_model()


class AccountsTest(TestCase):

    def test_user_creation_with_role(self):
        role = Role.objects.create(name="Detective")

        user = User.objects.create_user(
            username="detective1",
            email="detective1@test.com",
            password="pass123"
        )
        user.roles.add(role)

        self.assertEqual(user.username, "detective1")
        self.assertTrue(user.check_password("pass123"))
        self.assertIn(role, user.roles.all())