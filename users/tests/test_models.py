from django.test import TestCase


class UserModelTests(TestCase):
    def test_str_representation(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            email="user@example.com", password="StrongPass123"
        )
        self.assertEqual(str(user), "Email: user@example.com")
