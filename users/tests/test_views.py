from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticatedSystemTests(APITestCase):

    def test_authenticated_user_can_view_their_profile(self):
        User = get_user_model()
        User.objects.create_user(
            email="auth@user.com", password="ImAuthUser99"
        )
        url = "/users/token/"
        response = self.client.post(
            url, {"email": "auth@user.com", "password": "ImAuthUser99"}
        )

        access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        profile_response = self.client.get("/users/me/")

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], "auth@user.com")
        self.assertNotIn("password", profile_response.data)

    def test_authenticated_user_can_update_their_profile(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="try@update.com", password="111oldpassword"
        )
        url = "/users/token/"
        response = self.client.post(
            url, {"email": "try@update.com", "password": "111oldpassword"}
        )

        access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        update_url = "/users/me/"
        update_response = self.client.put(
            update_url,
            {"email": "new@updated.com", "password": "222newpassword"},
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["email"], "new@updated.com")
        user.refresh_from_db()
        self.assertTrue(user.check_password("222newpassword"))

    def test_unauthenticated_user_gets_401(self):

        url = "/users/me/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_gets_401_when_updating_profile(self):

        url = "/users/me/"

        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_first_name(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="patch@test.com", password="PatchPass123"
        )
        url = "/users/token/"
        response = self.client.post(
            url, {"email": "patch@test.com", "password": "PatchPass123"}
        )
        access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.patch("/users/me/", {"first_name": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Updated")
