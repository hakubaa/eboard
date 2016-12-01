import unittest
from unittest.mock import Mock, patch, ANY
import json
import email

from flask import url_for
from app import create_app, db
from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from flask_login import login_user

from app.mail.forms import LoginForm
from app.models import User

from tests.mail import imap_responses


@patch("app.mail.views.imap_clients")
@patch("app.mail.views.current_user")
class GetEmailsViewTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def mock_imap_client(self, iclients_mock):
        client_mock = Mock()
        iclients_mock.get.return_value = client_mock
        _, data = imap_responses.get_emails
        emails = []
        for item in data:
            if item == b')': continue   
            if isinstance(item, tuple):
                msg = email.message_from_string(item[1].decode())
                emails.append(msg)
        client_mock.get_emails.return_value = ("OK", emails)
        client_mock.len_mailbox.return_value = ("OK", 100)
        client_mock.select.return_value = ("OK", b'2044')
        return client_mock      

    def test_returns_error_status_when_noauth_user(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock)
        iclients_mock.get.return_value = None
        response = self.client.get(url_for("mail.imap_get_emails"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_calls_get_emails(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_get_emails"), 
                                           query_string = dict(ids="1,2"))
        self.assertTrue(client_mock.get_emails.called)

    def test_passes_ids_to_get_emails(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_get_emails"), 
                                           query_string = dict(ids="1,2"))
        client_mock.get_emails.assert_called_with("1,2")

    def test_returns_error_when_ids_not_specified(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_get_emails"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")        

    def test_returns_ok_status_when_ids_correct(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_get_emails"), 
                                           query_string = dict(ids="1,2"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "OK")    

    def test_returns_list_of_emails_in_data(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_get_emails"), 
                                           query_string = dict(ids="1,2"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertIsInstance(data["data"], list)
        self.assertEqual(len(data["data"]), 2)

    def test_calls_select_method(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        self.client.get(url_for("mail.imap_get_emails"), 
                                query_string=dict(ids="1,2", mailbox="Praca"))   
        client_mock.select.assert_called_once_with("Praca")
           
    def test_calls_select_method_with_default_mailbox(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock)
        self.client.get(url_for("mail.imap_get_emails"), 
                                query_string=dict(ids="1,2"))   
        client_mock.select.assert_called_once_with("INBOX")


@patch("app.mail.views.imap_clients")
@patch("app.mail.views.current_user")
class GetHeadersViewTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def mock_imap_client(self, iclients_mock,
                         response = imap_responses.get_headers2):
        client_mock = Mock()
        iclients_mock.get.return_value = client_mock
        client_mock.get_headers.return_value = response
        client_mock.len_mailbox.return_value = ("OK", 100)
        return client_mock

    def test_returns_error_status_when_noauth_user(
        self, user_mock, iclients_mock
    ):
        iclients_mock.get.return_value = False
        response = self.client.get(url_for("mail.imap_get_headers"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_calls_len_mailbox_with_proper_name(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock)  
        response = self.client.get(url_for("mail.imap_get_headers"),
                                   query_string = dict(mailbox="Praca"))
        client_mock.len_mailbox.assert_called_once_with("Praca")

    def test_calls_get_headers_with_the_proper_range(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock) 
        response = self.client.get(
            url_for("mail.imap_get_headers"),
            query_string = dict(mailbox="Praca", ids_from=0, ids_to=100)
        )
        client_mock.get_headers.assert_called_once_with(
            range(100, 0, -1), 
            fields = ["Subject", "Date", "From"]
        )

    def test_returns_list_with_headers(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock) 
        response = self.client.get(
            url_for("mail.imap_get_headers"),
            query_string = dict(mailbox="Praca", ids_from=0, ids_to=100)
        )
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "OK")
        self.assertEqual(len(data["data"]), 2)

    def test_returns_ok_when_empty_mailbox(
        self, user_mock, iclients_mock
    ):
        client_mock = self.mock_imap_client(iclients_mock) 
        client_mock.len_mailbox.return_value = ("OK", 0)
        response = self.client.get(
            url_for("mail.imap_get_headers"),
            query_string = dict(mailbox="Praca", ids_from=0, ids_to=100)
        )      
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "OK")


@patch("app.mail.views.imap_clients")
@patch("app.mail.views.current_user")
class ListViewTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def mock_imap_client(self, iclients_mock,
                          response=imap_responses.list_):
        client_mock = Mock()
        iclients_mock.get.return_value = client_mock
        client_mock.list.return_value = response
        return client_mock

    def test_for_calling_list_method(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_list"))
        self.assertTrue(client_mock.list.called)

    def test_returns_json_list_with_mailboxes(self, user_mock, iclients_mock):
        client_mock = self.mock_imap_client(iclients_mock)
        response = self.client.get(url_for("mail.imap_list"))
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
        response = self.client.get(url_for("mail.imap_list"))
        self.assertFalse(client_mock.list.called)

    def test_returns_error_status_when_noauth_user(
        self, user_mock, iclients_mock
    ):
        iclients_mock.get.return_value = False
        response = self.client.get(url_for("mail.imap_list"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")


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
    def test_for_passing_username_to_template(
        self, user_mock, imap_mock
    ):
        user_mock.id = 1
        imap_mock.return_value.state = "AUTH"
        imap_mock.return_value.username = "test@gmail.com"
        response = self.client.post(
            url_for("mail.login"), 
            data=dict(username="test@gmail.com", password="testowe", 
                      imap="imap.gmail.com"),
            follow_redirects = True
        )
        self.assert_context("username", "test@gmail.com")


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
