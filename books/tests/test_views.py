from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("book-list")

    def test_books_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
