import unittest
from unittest.mock import Mock, patch, ANY

from flask import url_for
from app import create_app, db
from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from flask_login import login_user

from app.mail.forms import LoginForm
from app.models import User

class MailViewsTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        user = User(email="test@gmail.com")
        user.password = "testowe"
        db.create_all()
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)

    def tearDown(self):
        db.drop_all()
        
    def test_for_login_url_resolving(self):
        response = self.client.get(url_for("mail.login"))
        self.assertEqual(response.status_code, 200)
        
    @unittest.skip
    def test_for_passing_form_to_view(self):
        response = self.client.get(url_for("mail.login"))
        self.assertIsInstance(self.get_context_variable("form"), LoginForm)

    @patch("app.mail.views.ImapClient")
    def test_for_redirecting_after_successfull_login(self, imap_mock):
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
