from rest_framework.test import APITestCase

from users.serializers import RegisterSerializer


class UserSerializerTests(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com", password="InitialPass123"
        )

    def test_register_user(self):
        from users.serializers import RegisterSerializer

        data = {"email": "newuser@example.com", "password": "StrongPass123"}
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("StrongPass123"))

    def test_update_email(self):
        from users.serializers import UserUpdateSerializer

        serializer = UserUpdateSerializer(
            instance=self.user, data={"email": "new@example.com"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, "new@example.com")

    def test_update_password(self):
        from users.serializers import UserUpdateSerializer

        serializer = UserUpdateSerializer(
            instance=self.user,
            data={"password": "NewStrongPass123"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertTrue(updated_user.check_password("NewStrongPass123"))

    def test_email_uniqueness_validation(self):
        from django.contrib.auth import get_user_model
        from users.serializers import UserUpdateSerializer

        User = get_user_model()
        User.objects.create_user(
            email="taken@example.com", password="SomePass123"
        )
        serializer = UserUpdateSerializer(
            instance=self.user,
            data={"email": "taken@example.com"},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_register_user_success_returns_user_without_password(self):
        serializer = RegisterSerializer(
            data={"email": "user@withoutparol.com", "password": "007BondJames"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "user@withoutparol.com")
        self.assertTrue(user.check_password("007BondJames"))
        self.assertNotIn("password", serializer.data)

    def test_user_serializer_read_only(self):
        from django.contrib.auth import get_user_model
        from users.serializers import UserSerializer

        User = get_user_model()
        serializer = UserSerializer(instance=self.user)
        self.assertEqual(serializer.data["email"], "user@example.com")
        self.assertIn("id", serializer.data)
        self.assertNotIn("password", serializer.data)
