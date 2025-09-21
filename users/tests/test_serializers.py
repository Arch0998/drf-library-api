from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from users.serializers import RegisterSerializer, UserSerializer


User = get_user_model()


class UserSerializerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="InitialPass123"
        )

    def test_register_user(self):
        data = {"email": "newuser@example.com", "password": "StrongPass123"}
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("StrongPass123"))

    def test_update_email(self):
        serializer = UserSerializer(
            instance=self.user,
            data={"email": "new@example.com"},
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, "new@example.com")

    def test_update_password(self):
        serializer = UserSerializer(
            instance=self.user,
            data={"password": "NewStrongPass123"},
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertTrue(updated_user.check_password("NewStrongPass123"))

    def test_email_uniqueness_validation(self):
        other_user = User.objects.create_user(
            email="taken@example.com",
            password="SomePass123"
        )
        serializer = UserSerializer(
            instance=self.user,
            data={"email": "taken@example.com"},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
