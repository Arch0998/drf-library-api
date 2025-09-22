from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model


class JWTAuthTests(APITestCase):
    def test_obtain_token(self):
        User = get_user_model()
        User.objects.create_user(
            email="obtain@token.com", password="password123"
        )

        url = "/users/token/"
        response = self.client.post(
            url, {"email": "obtain@token.com", "password": "password123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token(self):
        User = get_user_model()
        User.objects.create_user(
            email="refresh@token.com", password="password123"
        )

        obtain = self.client.post(
            "/users/token/",
            {"email": "refresh@token.com", "password": "password123"},
        )
        refresh = obtain.data["refresh"]

        response = self.client.post(
            "/users/token/refresh/", {"refresh": refresh}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
