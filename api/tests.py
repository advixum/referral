from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from .models import User


# Create your tests here.

class LoginViewTests(APITestCase):
    def test_invalid_phone_login(self):
        """
        Login attempt with an invalid phone number was unsuccessful.
        """
        response = self.client.post("/api/login/", {"phone": "+7 (123) 456-78-9"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": "Phone number must have exactly 11 digits."})

    def test_empty_phone_login(self):
        """
        Login attempt with an empty phone number was unsuccessful.
        """
        response = self.client.post("/api/login/", {"phone": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": "Phone number must have exactly 11 digits."})

    def test_non_number_input_login(self):
        """
        Login attempt with a string without numbers was unsuccessful. 
        """
        response = self.client.post("/api/login/", {"phone": "abcd"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": "Phone number must have exactly 11 digits."})

    def test_successful_login(self):
        """
        Login attempt with a valid phone number was successful.
        """
        response = self.client.post("/api/login/", {"phone": "+7 (123) 456-78-90"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["code"]), 4)

    def test_response_code(self):
        """
        The verification code sent in different requests was unique.
        """
        response1 = self.client.post("/api/login/", {"phone": "+7 (123) 456-78-90"})
        response2 = self.client.post("/api/login/", {"phone": "+7 (123) 456-78-90"})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response1.data["code"], response2.data["code"])

class VerifyViewTests(APITestCase):
    def test_invalid_code_response(self):
        """
        Invalid code was rejected.
        """
        data = {"phone": "+7 (123) 456-78-90", "code": "1234", "verify": "5678"}
        response = self.client.post("/api/verify/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": "Invalid code."})

    def test_successful_login_response(self):
        """
        Login attempt with an existing phone number was successful.
        """
        user = User.objects.create_user(username="71234567890")
        user.save()
        data = {"phone": "+7 (123) 456-78-90", "code": "1234", "verify": "1234"}
        response = self.client.post("/api/verify/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful.")
        self.assertIn("token", response.data)

    def test_user_creation_and_login_response(self):
        """
        Registration and login attempt with a non-existent phone number
        was successful. 
        """
        data = {"phone": "+7 (123) 000-00-00", "code": "1234", "verify": "1234"}
        response = self.client.post("/api/verify/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User created and logged in.")
        self.assertIn("token", response.data)

class DataViewTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="11111111111")
        self.user2 = User.objects.create_user(username="22222222222")
        self.user3 = User.objects.create_user(username="33333333333")
        self.user2.invited = self.user1.ref
        self.user2.save()
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token3 = Token.objects.create(user=self.user3)

    def test_not_auth_get_request(self):
        """
        Unauthorized GET request was rejected.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {''}")
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_auth_post_request(self):
        """
        Unauthorized POST request was rejected.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {''}")
        response = self.client.post("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user1_data(self):
        """
        The data of the user who invited other users was correct.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [self.user2.username])
        self.assertEqual(response.data["ref"], self.user1.ref)
        self.assertEqual(response.data["invited"], "")

    def test_get_user2_data(self):
        """
        The details of the user invited by another user was correct.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [])
        self.assertEqual(response.data["ref"], self.user2.ref)
        self.assertEqual(response.data["invited"], self.user1.ref)

    def test_get_user3_data(self):
        """
        The data of a user who did not invite other users and did not
        register a referral was correct. 
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token3.key}")
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [])
        self.assertEqual(response.data["ref"], self.user3.ref)
        self.assertEqual(response.data["invited"], "")

    def test_post_user3_ref_user1(self):
        """
        Registration of an existing referral was successful.
        """
        # Check user3 POST request data
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token3.key}")
        response = self.client.post("/api/data/", data={"ref_code": self.user1.ref})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], f"Referral code {self.user1.ref} successfully registered.")
        self.assertEqual(response.data["invited"], self.user1.ref)
        # Check user3 GET request data
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [])
        self.assertEqual(response.data["ref"], self.user3.ref)
        self.assertEqual(response.data["invited"], self.user1.ref)
        # Check user1 GET request data
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [self.user2.username, self.user3.username])
        self.assertEqual(response.data["ref"], self.user1.ref)
        self.assertEqual(response.data["invited"], "")

    def test_post_user3_ref_user3(self):
        """
        Registration of your own referral was unsuccessful.
        """
        # Check user3 POST request data
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token3.key}")
        response = self.client.post("/api/data/", data={"ref_code": self.user3.ref})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You cannot invite yourself.")
        # Check user3 GET request data
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [])
        self.assertEqual(response.data["ref"], self.user3.ref)
        self.assertNotEqual(response.data["invited"], self.user3.ref)

    def test_post_user3_ref_not_exists(self):
        """
        Registration of a non-existing referral was unsuccessful.
        """
        # Check user3 POST request data
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token3.key}")
        response = self.client.post("/api/data/", data={"ref_code": "not_exists"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No such code exists.")
        # Check user3 GET request data
        response = self.client.get("/api/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"], [])
        self.assertEqual(response.data["ref"], self.user3.ref)
        self.assertEqual(response.data["invited"], "")

    def test_post_user3_ref_empty(self):
        """
        Registration of an empty referral was unsuccessful.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token3.key}")
        response = self.client.post("/api/data/", data={"ref_code": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Referral code is required.")
