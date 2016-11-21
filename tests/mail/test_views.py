import unittest
from unittest.mock import Mock, patch, ANY
import json

from flask import url_for
from app import create_app, db
from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from flask_login import login_user

from app.mail.forms import LoginForm
from app.models import User

from tests.mail import imap_responses

@patch("app.mail.views.imap_clients")
@patch("app.mail.views.current_user")
class MailAjaxViewsTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def mock_imap_client(self, iclients_mock,
                          response=imap_responses.list_mailbox):
        client_mock = Mock()
        iclients_mock.get.return_value = client_mock
        client_mock.list.return_value = response
        return client_mock

    def test_for_calling_list_method(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_list_mailbox"))
        self.assertTrue(client_mock.list.called)

    def test_returns_json_list_with_mailboxes(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_list_mailbox"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "OK")
        self.assertIn("INBOX", data["data"])
        self.assertIn("Praca", data["data"])

    def test_for_not_calling_list_method_when_noauth_user(
        self, user_mock, iclients_mock
    ):
        client_mock = Mock()
        client_mock.list = Mock()
        iclients_mock.get.return_value = False
        response = self.client.get(url_for("mail.imap_list_mailbox"))
        self.assertFalse(client_mock.list.called)

    def test_returns_error_status_when_noauth_user(
        self, user_mock, iclients_mock
    ):
        iclients_mock.get.return_value = False
        response = self.client.get(url_for("mail.imap_list_mailbox"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")


@unittest.skip
class MailViewsTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def test_for_login_url_resolving(self):
        response = self.client.get(url_for("mail.login"))
        self.assertEqual(response.status_code, 200)

    def test_for_passing_form_to_view(self):
        response = self.client.get(url_for("mail.login"))
        self.assertIsInstance(self.get_context_variable("form"), LoginForm)

    @patch("app.mail.views.ImapClient")
    @patch("app.mail.views.current_user")
    def test_for_redirecting_after_successfull_login(self, user_mock, imap_mock):
        user_mock.id = 1
        imap_mock.return_value.state = "AUTH"
        response = self.client.post(
            url_for("mail.login"), 
            data=dict(username="test@gmail.com", password="testowe", 
                      imap="imap.gmail.com")
        )
        self.assertRedirects(response, url_for("mail.client"))

    @patch("app.mail.views.ImapClient")
    def test_for_passing_imap_addr_to_imapclient(self, imap_mock):
        response = self.client.post(
            url_for("mail.login"), 
            data=dict(username="test@gmail.com", password="testowe", 
                      imap="imap.gmail.com")
        )
        imap_mock.assert_called_with("imap.gmail.com", timeout=ANY)        

    @patch("app.mail.views.ImapClient")
    def test_for_passing_username_and_pass_to_imapclient(self, imap_mock):
        login_mock = Mock()
        imap_mock.return_value.login = login_mock

        response = self.client.post(
            url_for("mail.login"), 
            data=dict(username="test@gmail.com", password="testowe", 
                      imap="imap.gmail.com")
        )
        login_mock.assert_called_with("test@gmail.com", "testowe")   

    @patch("app.mail.views.ImapClient")
    @patch("app.mail.views.current_user")
    def test_for_rendering_proper_template_after_login(
        self, user_mock, imap_mock
    ):
        user_mock.id = 1
        imap_mock.return_value.state = "AUTH"
        response = self.client.post(
            url_for("mail.login"), 
            data=dict(username="test@gmail.com", password="testowe", 
                      imap="imap.gmail.com"),
            follow_redirects = True
        )
        self.assert_template_used("mail/client.html")

    @patch("app.mail.views.ImapClient")
    @patch("app.mail.views.current_user")
    def test_for_redirectiong_for_unlogged_users(
        self, user_mock, imap_mock
    ):
        user_mock.id = 5
        response = self.client.get(url_for("mail.client"))
        self.assertRedirects(response, url_for("mail.login"))

    @unittest.skip
    @patch("app.mail.views.ImapClient")
    def test_for_saving_imapclient_in_app_context(self, imap_mock):
        imap_mock.return_value.state = "AUTH"
        client_mock = Mock()
        imap_mock.return_value = client_mock

        response = self.client.post(
            url_for("mail.login"), 
            data=dict(username="test@gmail.com", password="testowe", 
                      imap="imap.gmail.com")
        )
        self.assertEqual(g_mock.imap_client, client_mock)
