#To Run: python manage.py test

import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Task, UserTask, Leaderboard, Profile
from .views import (
    email_validation,
    register_user,
    login_user,
    tasks,
    complete_task,
    leaderboard,
    get_user_profile,
    update_user_profile,
    user_rank
)

User = get_user_model()

class ViewsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user and associated leaderboard entry.
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            email="test@exeter.ac.uk"
        )
        self.leaderboard = Leaderboard.objects.create(user=self.user, points=0)
        # Create a sample task for testing complete_task.
        # Removed the 'requiresUpload' and 'requireScan' fields.
        self.task = Task.objects.create(
            id=1,
            description="Sample Task",
            points=10
        )
        # Ensure a Profile exists for the user.
        Profile.objects.get_or_create(user=self.user)

    def test_update_user_profile_with_picture(self):
        url = reverse('update_user_profile')
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        data = {"profile_picture": image}
        response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.profile_picture)

    def test_update_user_profile_empty_payload(self):
        url = reverse('update_user_profile')
        response = self.client.put(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "profileuser")
        self.assertEqual(self.user.email, "profile@exeter.ac.uk")

    def test_update_user_profile_with_invalid_file(self):
        url = reverse('update_user_profile')
        fake_file = SimpleUploadedFile("test.txt", b"fake content", content_type="text/plain")
        data = {"profile_picture": fake_file}
        response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class EmailValidationTests(TestCase):
    def test_email_validation_valid(self):
        self.assertTrue(email_validation("user@exeter.ac.uk"))

    def test_email_validation_valid_uppercase(self):
        self.assertTrue(email_validation("USER@EXETER.AC.UK"))

    def test_email_validation_invalid_domain(self):
        self.assertFalse(email_validation("user@gmail.com"))
        self.assertFalse(email_validation("user@domain.com"))

    def test_email_validation_invalid_format(self):
        invalid_emails = [
            "userexeter.ac.uk",       # missing '@'
            "user@@exeter.ac.uk",     # double '@'
            "user@exeter",            # missing domain extension
            "user@exeter..ac.uk",     # double dots in domain
            "user@.ac.uk",            # missing domain name before dot
            "user@exetercom",         # missing dot in domain extension
            " user@exeter.ac.uk",     # leading whitespace
            "user@exeter.ac.uk ",     # trailing whitespace
            "user @exeter.ac.uk",     # space in local part
            ""                        # empty string
        ]
        for email in invalid_emails:
            self.assertFalse(email_validation(email), f"Email '{email}' should be invalid")

    # ---------- Registration Tests ----------
    def test_register_missing_fields(self):
        data = {"username": "", "password": "", "passwordagain": "", "email": ""}
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_register_passwords_mismatch(self):
        data = {
            "username": "newuser",
            "password": "pass1",
            "passwordagain": "pass2",
            "email": "newuser@exeter.ac.uk"
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data.get("error", ""))

    def test_register_invalid_email(self):
        data = {
            "username": "newuser",
            "password": "pass1",
            "passwordagain": "pass1",
            "email": "newuser@gmail.com"
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please use your @exeter.ac.uk email only", response.data.get("error", ""))

    def test_register_existing_username(self):
        data = {
            "username": "testuser",  # already exists
            "password": "testpassword",
            "passwordagain": "testpassword",
            "email": "unique@exeter.ac.uk"
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Username already taken", response.data.get("error", ""))

    def test_register_existing_email(self):
        data = {
            "username": "uniqueuser",
            "password": "testpassword",
            "passwordagain": "testpassword",
            "email": "test@exeter.ac.uk"  # already used
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This email is already registered", response.data.get("error", ""))

    def test_register_success(self):
        data = {
            "username": "newuser",
            "password": "testpassword",
            "passwordagain": "testpassword",
            "email": "newuser@exeter.ac.uk"
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertEqual(response.data.get("message"), "User registered successfully!")
        # Verify that a Leaderboard entry was created for the new user.
        new_user = User.objects.get(username="newuser")
        self.assertTrue(Leaderboard.objects.filter(user=new_user).exists())

    # ---------- Login Tests ----------
    def test_login_missing_fields(self):
        data = {}
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_login_invalid_credentials(self):
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_login_success(self):
        data = {"username": "testuser", "password": "testpassword"}
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data.get("user"), "testuser")

    # ---------- Tasks Tests ----------
    def test_tasks(self):
        # Create an additional task.
        Task.objects.create(
            id=2,
            description="Task 2",
            points=5
        )
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Expect at least one task to be present.
        self.assertGreaterEqual(len(response.data), 1)

    # ---------- Complete Task Tests ----------
    def test_complete_task_success(self):
        self.client.force_authenticate(user=self.user)
        # Create a new task for completion.
        new_task = Task.objects.create(
            id=3,
            description="New Task",
            points=20
        )
        response = self.client.post('/complete_task/', {"task_id": new_task.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("points", response.data)
        # Verify that leaderboard points are updated.
        self.leaderboard.refresh_from_db()
        self.assertEqual(self.leaderboard.points, new_task.points)

    def test_complete_task_already_completed(self):
        self.client.force_authenticate(user=self.user)
        # First attempt: complete the task.
        response1 = self.client.post('/complete_task/', {"task_id": self.task.id})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        # Second attempt: should return error.
        response2 = self.client.post('/complete_task/', {"task_id": self.task.id})
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Task already completed", response2.data.get("message", ""))

    def test_complete_task_missing_task_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/complete_task/', {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_task_nonexistent_task(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/complete_task/', {"task_id": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_task_auth_required(self):
        # Ensure endpoint is protected.
        self.client.force_authenticate(user=None)
        response = self.client.post('/complete_task/', {"task_id": self.task.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- Leaderboard Tests ----------
    def test_leaderboard_order(self):
        # Create another user with higher points.
        user2 = User.objects.create_user(
            username="user2",
            password="password2",
            email="user2@exeter.ac.uk"
        )
        Leaderboard.objects.create(user=user2, points=50)
        response = self.client.get('/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if len(response.data) >= 2:
            # The user with higher points (user2) should appear first.
            self.assertEqual(response.data[0]["user"], user2.username)

    # ---------- Get User Profile Tests ----------
    def test_get_user_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        # Create a completed task and set leaderboard points.
        from .models import UserTask  # import here if not imported at the top
        UserTask.objects.create(user=self.user, task=self.task, completed=True)
        self.leaderboard.points = 10
        self.leaderboard.save()
        response = self.client.get('/user/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["total_points"], 10)
        self.assertEqual(response.data["completed_tasks"], 1)
        self.assertEqual(response.data["leaderboard_rank"], user_rank(10))

    def test_get_user_profile_auth_required(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/user/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- User Rank Tests ----------
    def test_user_rank_beginner(self):
        self.assertEqual(user_rank(10), "Beginner")

    def test_user_rank_intermediate(self):
        self.assertEqual(user_rank(100), "Intermediate")

    def test_user_rank_expert(self):
        self.assertEqual(user_rank(1300), "Expert")

    # ---------- Update User Profile Tests ----------
    def test_update_user_profile_without_picture(self):
        self.client.force_authenticate(user=self.user)
        new_username = "updateduser"
        new_email = "updateduser@example.com"
        data = {"username": new_username, "email": new_email}
        response = self.client.put('/user/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("message"), "Profile updated successfully")
        # Refresh the user from the database.
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, new_username)
        self.assertEqual(self.user.email, new_email)

    def test_update_user_profile_with_picture(self):
        self.client.force_authenticate(user=self.user)
        new_username = "updatedwithpic"
        new_email = "updatedwithpic@example.com"
        # Create a dummy image file.
        image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # Minimal JPEG header bytes.
        image = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpeg")
        data = {"username": new_username, "email": new_email, "profile_picture": image}
        response = self.client.put('/user/update/', data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("message"), "Profile updated successfully")
        # Refresh the user and profile from the database.
        self.user.refresh_from_db()
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(self.user.username, new_username)
        self.assertEqual(self.user.email, new_email)
        # Check that a profile picture has been saved.
        self.assertTrue(profile.profile_picture)
