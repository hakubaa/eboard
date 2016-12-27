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
from app.mail.client import ImapClientError

from tests.mail import imap_responses

@patch("app.mail.views.ImapClient")
class CSearchTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def login_imap_client(self, username="Testowy", password="Testowe"):
         with self.client.session_transaction() as sess:
            sess["imap_username"] = username
            sess["imap_password"] = password 
            sess["imap_addr"] = "testowy"  

    def mock_csearch(self, imap_client, response = ("OK", ['1', '2', '3'])):
        mock = Mock()
        mock.return_value = response
        imap_client.return_value.csearch = mock
        return mock

    def test_returns_error_for_not_authenticated_users(self, mock_client):
        mock = self.mock_csearch(mock_client)
        response = self.client.get(url_for("mail.imap_search"),
                            query_string=dict(
                                mailbox="INBOX",
                                criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                            )
                   )
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_calls_csearch_method(self, mock_client):
        mock = self.mock_csearch(mock_client)
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX",
                            criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                        )
                   )  
        self.assertTrue(mock.called)     

    def test_for_passing_args_to_csearch_method(self, mock_client):
        mock = self.mock_csearch(mock_client)
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX",
                            criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                        )
                   )  
        mock.assert_called_with([{"key":"SUBJECT","value":"Test","decode":True}])

    def test_returns_error_when_no_mailbox(self, mock_client):
        mock = self.mock_csearch(mock_client)
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_search"),
                            query_string=dict(
                                criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                            )
                   )
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_no_criteria(self, mock_client):
        mock = self.mock_csearch(mock_client)
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX"
                        )
                   )  
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_csearch_method_fails(self, mock_client):
        mock = self.mock_csearch(mock_client, response=("NO", ["FUCK"]))
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX",
                            criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                        )
                   )  
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_csearch_method_error(self, mock_client):
        mock = self.mock_csearch(mock_client)
        mock.side_effect = ImapClientError
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX",
                            criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                        )
                   )  
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_for_calling_select_method(self, mock_client):
        mock = self.mock_csearch(mock_client)
        select_mock = Mock()
        select_mock.return_value = ("OK", "WORK")
        mock_client.return_value.select = select_mock
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX2",
                            criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                        )
                   )  
        select_mock.assert_called_with('"INBOX2"')

     
    def test_for_returning_error_when_select_fails(self, mock_client):
        mock = self.mock_csearch(mock_client)
        select_mock = Mock()
        select_mock.return_value = ("OK", "WORK")
        select_mock.side_effect = ImapClientError
        mock_client.return_value.select = select_mock
        self.login_imap_client()
        response = self.client.get(
                        url_for("mail.imap_search"),
                        query_string=dict(
                            mailbox="INBOX2",
                            criteria='[{"key":"SUBJECT","value":"Test","decode":true}]'
                        )
                   )  
        select_mock.assert_called_with('"INBOX2"')

        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(select_mock.called)
        self.assertEqual(data["status"], "ERROR")


# @patch("app.mail.views.ImapClient")
# class RenameMailboxTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def login_imap_client(self, username="Testowy", password="Testowe"):
#          with self.client.session_transaction() as sess:
#             sess["imap_username"] = username
#             sess["imap_password"] = password 
#             sess["imap_addr"] = "testowy"  

#     def mock_rename(self, mock_client, response = ("OK", ["INFO"])):
#         mock = Mock()
#         mock.return_value = response
#         mock_client.return_value.rename = mock
#         return mock

#     def test_returns_error_for_not_authenticated_users(self, mock_client):
#         self.mock_rename(mock_client)
#         response = self.client.get(url_for("mail.imap_rename"),
#                         query_string=dict(oldmailbox="INBOX",
#                                           newmailbox="NEW_INBOX"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_calls_rename_method(self, mock_client):
#         mock = self.mock_rename(mock_client)
#         self.login_imap_client()
#         self.client.get(url_for("mail.imap_rename"),
#                         query_string=dict(oldmailbox="INBOX",
#                                           newmailbox="NEW_INBOX"))
#         mock.assert_called_with("INBOX", "NEW_INBOX")
     

#     def test_returns_error_when_no_oldmailbox(self, mock_client):
#         mock = self.mock_rename(mock_client)
#         self.login_imap_client()
#         response = self.client.get(url_for("mail.imap_rename"),
#                         query_string=dict(newmailbox="NEW_INBOX"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_returns_error_when_no_newmailbox(self, mock_client):
#         mock = self.mock_rename(mock_client)
#         self.login_imap_client()
#         response = self.client.get(url_for("mail.imap_rename"),
#                         query_string=dict(oldmailbox="NEW_INBOX"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_returns_error_when_rename_method_fails(self, mock_client):
#         mock = self.mock_rename(mock_client, response=("NO", ["FUCK"]))
#         self.login_imap_client()
#         response = self.client.get(url_for("mail.imap_rename"),
#                         query_string=dict(oldmailbox="INBOX",
#                                           newmailbox="NEW_INBOX"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_returns_error_when_rename_method_error(self, mock_client):
#         mock = self.mock_rename(mock_client, response=("OK", ["WOW"]))
#         mock.side_effect = ImapClientError
#         self.login_imap_client()
#         response = self.client.get(url_for("mail.imap_rename"),
#                         query_string=dict(oldmailbox="INBOX",
#                                           newmailbox="NEW_INBOX"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")


@patch("app.mail.views.ImapClient")
class StoreTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def login_imap_client(self, username="Testowy", password="Testowe"):
         with self.client.session_transaction() as sess:
            sess["imap_username"] = username
            sess["imap_password"] = password 
            sess["imap_addr"] = "testowy"  

    def mock_store(self, mock_client, response = ("OK", "INFO"), 
                   command="store"):
        flags_mock = Mock()
        flags_mock.return_value = response
        setattr(mock_client.return_value, command, flags_mock)
        return flags_mock

    def test_returns_error_for_not_authenticated_users(self, mock_client):
        self.mock_store(mock_client, command="store")
        response = self.client.get(url_for("mail.imap_store", command="add"),
                        query_string=dict(ids="1", mailbox="INBOX",
                                          flags="\\Flagged"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_calls_add_flags_method(self, mock_client):
        add_flags_mock = self.mock_store(mock_client, command="add_flags")
        self.login_imap_client()
        self.client.get(url_for("mail.imap_store", command="add"),
                        query_string=dict(ids="1", mailbox="INBOX",
                                          flags="\\Flagged"))
        add_flags_mock.assert_called_with("1", "\\Flagged")

    def test_calls_remove_flags_method(self, mock_client):
        flags_mock = self.mock_store(mock_client, command="remove_flags")
        self.login_imap_client()
        self.client.get(url_for("mail.imap_store", command="remove"),
                        query_string=dict(ids="1", mailbox="INBOX",
                                          flags="\\Flagged"))
        flags_mock.assert_called_with("1", "\\Flagged")

    def test_calls_set_flags_method(self, mock_client):
        flags_mock = self.mock_store(mock_client, command="set_flags")
        self.login_imap_client()
        self.client.get(url_for("mail.imap_store", command="set"),
                        query_string=dict(ids="1", mailbox="INBOX",
                                          flags="\\Flagged"))
        flags_mock.assert_called_with("1", "\\Flagged")       

    def test_returns_error_when_improper_command(self, mock_client):
        flags_mock = self.mock_store(mock_client, command="set_flags")
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_store", command="delete"),
                                   query_string=dict(ids="1", mailbox="INBOX",
                                                     flags="\\Flagged"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_no_ids(self, mock_client):
        flags_mock = self.mock_store(mock_client, command="set_flags")
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_store", command="set"),
                                   query_string=dict(mailbox="INBOX",
                                                     flags="\\Flagged"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_no_flags(self, mock_client):
        flags_mock = self.mock_store(mock_client, command="set_flags")
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_store", command="set"),
                                   query_string=dict(ids="1", mailbox="INBOX"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_no_mailbox(self, mock_client):
        flags_mock = self.mock_store(mock_client, command="set_flags")
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_store", command="set"),
                                   query_string=dict(ids="1", flags="INBOX"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_for_calling_select_method(self, mock_client):
        flags_mock = self.mock_store(mock_client, response=("OK", "YUPI"),
                                     command="add_flags")
        select_mock = Mock()
        select_mock.return_value = ("OK", "WORK")
        mock_client.return_value.select = select_mock
        self.login_imap_client()
        self.client.get(url_for("mail.imap_store", command="add"),
                        query_string=dict(ids="1", mailbox="INBOX2",
                                          flags="\\Flagged"))  
        select_mock.assert_called_with('"INBOX2"')


    def test_for_returning_error_when_select_fails(self, mock_client):
        flags_mock = self.mock_store(mock_client, response=("OK", "YUPI"),
                                     command="add")

        select_mock = Mock()
        select_mock.return_value = ("NO", "FUCK")
        select_mock.side_effect = ImapClientError
        mock_client.return_value.select = select_mock

        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_store", command="add"),
                                   query_string=dict(ids="1", mailbox="INBOX",
                                                     flags="\\Flagged"))    
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(select_mock.called)
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_store_method_fails(self, mock_client):
        flags_mock = self.mock_store(mock_client, response=("NO", ["FUCK"]),
                                     command="add_flags")  
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_store", command="add"),
                                   query_string=dict(ids="1", flags="\\FLagged",
                                                     mailbox="INBOX"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")


@patch("app.mail.views.ImapClient")
class MoveEmailsTest(TestCase):

    def create_app(self):
        return create_app("testing")

    def login_imap_client(self, username="Testowy", password="Testowe"):
         with self.client.session_transaction() as sess:
            sess["imap_username"] = username
            sess["imap_password"] = password 
            sess["imap_addr"] = "testowy"  

    def mock_imap_client(self, mock_client, response = ("OK", "INFO")):
        move_mock = Mock()
        move_mock.return_value = response
        mock_client.return_value.move_emails = move_mock
        return move_mock     
            
    def test_returns_error_for_not_authenticated_users(self, mock_client):
        self.mock_imap_client(mock_client)
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", dest_mailbox="INBOX",
                                              source_mailbox="INBOX2"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_ok_for_authenticated_users(self, mock_client):
        self.mock_imap_client(mock_client)
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", dest_mailbox="INBOX",
                                              source_mailbox="INBOX2"))
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "OK")    

    def test_calls_move_emails_method(self, mock_client):
        move_mock = self.mock_imap_client(mock_client)
        self.login_imap_client()
        self.client.get(url_for("mail.imap_move_emails"),
                        query_string=dict(ids="1", dest_mailbox="INBOX",
                                          source_mailbox="INBOX2"))
        self.assertTrue(move_mock.called)

    def test_passes_arguments_to_move_emails_method(self, mock_client):
        move_mock = self.mock_imap_client(mock_client)
        self.login_imap_client()
        self.client.get(url_for("mail.imap_move_emails"),
                        query_string=dict(ids="1", dest_mailbox="INBOX",
                                          source_mailbox="INBOX2"))
        move_mock.assert_called_with("1", '"INBOX"')

    def test_returns_error_when_no_ids(self, mock_client):
        move_mock = self.mock_imap_client(mock_client)
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(dest_mailbox="INBOX", 
                                              source_mailbox="INBOX2"))       
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_no_dest_mailbox(self, mock_client):
        move_mock = self.mock_imap_client(mock_client)
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", source_mailbox="INBOX2"))       
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")

    def test_returns_error_when_no_imap_response(self, mock_client):
        move_mock = self.mock_imap_client(mock_client, ("NO", "FUCK"))
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", dest_mailbox="INBOX",
                                              source_mailobx="INBOX2"))       
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")       

    def test_returns_status_and_data_when_success(self, mock_client):
        move_mock = self.mock_imap_client(mock_client, ("OK", "YUPI"))
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", dest_mailbox="INBOX",
                                              source_mailbox="INBOX2"))       
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "OK")
        self.assertEqual(data["data"], "YUPI")    

    def test_for_calling_select_method(self, mock_client):
        move_mock = self.mock_imap_client(mock_client, ("OK", "YUPI"))
        select_mock = Mock()
        select_mock.return_value = ("OK", "WORK")
        mock_client.return_value.select = select_mock
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", dest_mailbox="INBOX",
                                              source_mailbox="INBOX2"))       
        select_mock.assert_called_with('"INBOX2"')

    def test_for_returning_error_when_select_fails(self, mock_client):
        move_mock = self.mock_imap_client(mock_client, ("OK", "YUPI"))
        select_mock = Mock()
        select_mock.return_value = ("NO", "FUCK")
        select_mock.side_effect = ImapClientError
        mock_client.return_value.select = select_mock
        self.login_imap_client()
        response = self.client.get(url_for("mail.imap_move_emails"),
                            query_string=dict(ids="1", dest_mailbox="INBOX",
                                              source_mailbox="INBOX2"))       
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(data["status"], "ERROR")




# @patch("app.mail.views.ImapClient")
# class GetEmailTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def login_imap_client(self, username="Testowy", password="Testowe"):
#          with self.client.session_transaction() as sess:
#             sess["imap_username"] = username
#             sess["imap_password"] = password 
#             sess["imap_addr"] = "testowy"     

#     def mock_imap_client(self, mock_client):
#         mock = Mock()
#         mock.get_emails.return_value = ("OK", ["EMAIL"])
#         mock.select.return_value = ("OK", b'1')
#         mock_client.return_value = mock    
#         return mock

#     def test_returns_error_for_not_authenticated_users(self, mock_client):
#         response = self.client.get(url_for("mail.imap_get_email"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_returns_ok_for_authenticated_users(self, mock_client):
#         self.login_imap_client()
#         self.mock_imap_client(mock_client)
#         response = self.client.get(url_for("mail.imap_get_email"),
#                                    query_string=dict(id='1'))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "OK")      

#     def test_calls_get_emails_with_proper_id(self, mock_client):
#         self.login_imap_client()
#         mock = self.mock_imap_client(mock_client)
#         response = self.client.get(url_for("mail.imap_get_email"),
#                                    query_string=dict(id='1'))
#         mock.get_emails.assert_called_with('1')

#     @patch("app.mail.views.process_email_for_display")
#     def test_calls_process_email_for_display(self, mock_process, mock_client):
#         self.login_imap_client()
#         self.mock_imap_client(mock_client)
#         mock_process.return_value = None
#         response = self.client.get(url_for("mail.imap_get_email"),
#                                    query_string=dict(id='1'))
#         mock_process.assert_called_with("EMAIL")


# @patch("app.mail.views.imap_clients")
# @patch("app.mail.views.current_user")
# class GetEmailViewTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def mock_imap_client(self, iclients_mock):
#         client_mock = Mock()
#         iclients_mock.get.return_value = client_mock
#         _, data = imap_responses.get_emails
#         emails = []
#         for item in data:
#             if item == b')': continue   
#             if isinstance(item, tuple):
#                 msg = email.message_from_string(item[1].decode())
#                 emails.append(msg)
#         client_mock.get_emails.return_value = ("OK", emails)
#         client_mock.len_mailbox.return_value = ("OK", 100)
#         client_mock.select.return_value = ("OK", b'2044')
#         return client_mock    

#     def test_returns_error_status_when_noauth_user(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)
#         iclients_mock.get.return_value = None
#         response = self.client.get(url_for("mail.imap_get_email"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")



# @patch("app.mail.views.imap_clients")
# @patch("app.mail.views.current_user")
# class GetRawEmailsViewTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def mock_imap_client(self, iclients_mock):
#         client_mock = Mock()
#         iclients_mock.get.return_value = client_mock
#         _, data = imap_responses.get_emails
#         emails = []
#         for item in data:
#             if item == b')': continue   
#             if isinstance(item, tuple):
#                 msg = email.message_from_string(item[1].decode())
#                 emails.append(msg)
#         client_mock.get_emails.return_value = ("OK", emails)
#         client_mock.len_mailbox.return_value = ("OK", 100)
#         client_mock.select.return_value = ("OK", b'2044')
#         return client_mock      

#     def test_returns_error_status_when_noauth_user(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)
#         iclients_mock.get.return_value = None
#         response = self.client.get(url_for("mail.imap_get_raw_emails"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_calls_get_emails(self, user_mock, iclients_mock):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_get_raw_emails"), 
#                                            query_string = dict(ids="1,2"))
#         self.assertTrue(client_mock.get_emails.called)

#     def test_passes_ids_to_get_emails(self, user_mock, iclients_mock):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_get_raw_emails"), 
#                                            query_string = dict(ids="1,2"))
#         client_mock.get_emails.assert_called_with("1,2")

#     def test_returns_error_when_ids_not_specified(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_get_raw_emails"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")        

#     def test_returns_ok_status_when_ids_correct(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_get_raw_emails"), 
#                                            query_string = dict(ids="1,2"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "OK")    

#     def test_returns_list_of_emails_in_data(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_get_raw_emails"), 
#                                            query_string = dict(ids="1,2"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertIsInstance(data["data"], list)
#         self.assertEqual(len(data["data"]), 2)

#     def test_calls_select_method(self, user_mock, iclients_mock):
#         client_mock = self.mock_imap_client(iclients_mock)
#         self.client.get(url_for("mail.imap_get_raw_emails"), 
#                                 query_string=dict(ids="1,2", mailbox="Praca"))   
#         client_mock.select.assert_called_once_with("Praca")
           
#     def test_calls_select_method_with_default_mailbox(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)
#         self.client.get(url_for("mail.imap_get_raw_emails"), 
#                                 query_string=dict(ids="1,2"))   
#         client_mock.select.assert_called_once_with("INBOX")


# @patch("app.mail.views.imap_clients")
# @patch("app.mail.views.current_user")
# class GetHeadersViewTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def mock_imap_client(self, iclients_mock,
#                          response = imap_responses.get_headers2):
#         client_mock = Mock()
#         iclients_mock.get.return_value = client_mock
#         client_mock.get_headers.return_value = response
#         client_mock.len_mailbox.return_value = ("OK", 100)
#         return client_mock

#     def test_returns_error_status_when_noauth_user(
#         self, user_mock, iclients_mock
#     ):
#         iclients_mock.get.return_value = False
#         response = self.client.get(url_for("mail.imap_get_headers"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")

#     def test_calls_len_mailbox_with_proper_name(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock)  
#         response = self.client.get(url_for("mail.imap_get_headers"),
#                                    query_string = dict(mailbox="Praca"))
#         client_mock.len_mailbox.assert_called_once_with('"Praca"')

#     def test_calls_get_headers_with_the_proper_range(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock) 
#         response = self.client.get(
#             url_for("mail.imap_get_headers"),
#             query_string = dict(mailbox="Praca", ids_from=0, ids_to=100)
#         )
#         client_mock.get_headers.assert_called_once_with(
#             range(100, 0, -1), 
#             fields = ["Subject", "Date", "From"]
#         )

#     def test_returns_list_with_headers(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock) 
#         response = self.client.get(
#             url_for("mail.imap_get_headers"),
#             query_string = dict(mailbox="Praca", ids_from=0, ids_to=100)
#         )
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "OK")
#         self.assertEqual(len(data["data"]), 2)

#     def test_returns_ok_when_empty_mailbox(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = self.mock_imap_client(iclients_mock) 
#         client_mock.len_mailbox.return_value = ("OK", 0)
#         response = self.client.get(
#             url_for("mail.imap_get_headers"),
#             query_string = dict(mailbox="Praca", ids_from=0, ids_to=100)
#         )      
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "OK")


# @patch("app.mail.views.imap_clients")
# @patch("app.mail.views.current_user")
# class ListViewTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def mock_imap_client(self, iclients_mock,
#                           response=imap_responses.list_):
#         client_mock = Mock()
#         iclients_mock.get.return_value = client_mock
#         client_mock.list.return_value = response
#         return client_mock

#     def test_for_calling_list_method(self, user_mock, iclients_mock):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_list"))
#         self.assertTrue(client_mock.list.called)

#     def test_returns_json_list_with_dics(self, user_mock, iclients_mock):
#         client_mock = self.mock_imap_client(iclients_mock)
#         response = self.client.get(url_for("mail.imap_list"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "OK")
#         self.assertIn({"utf7": "INBOX", "utf16": "INBOX"}, data["data"])
#         self.assertIn({"utf7": "Praca", "utf16": "Praca"}, data["data"])

#     def test_for_not_calling_list_method_when_noauth_user(
#         self, user_mock, iclients_mock
#     ):
#         client_mock = Mock()
#         client_mock.list = Mock()
#         iclients_mock.get.return_value = False
#         response = self.client.get(url_for("mail.imap_list"))
#         self.assertFalse(client_mock.list.called)

#     def test_returns_error_status_when_noauth_user(
#         self, user_mock, iclients_mock
#     ):
#         iclients_mock.get.return_value = False
#         response = self.client.get(url_for("mail.imap_list"))
#         data = json.loads(response.data.decode("utf-8"))
#         self.assertEqual(data["status"], "ERROR")


# class MailViewsTest(TestCase):

#     def create_app(self):
#         return create_app("testing")

#     def test_for_login_url_resolving(self):
#         response = self.client.get(url_for("mail.login"))
#         self.assertEqual(response.status_code, 200)

#     def test_for_passing_form_to_view(self):
#         response = self.client.get(url_for("mail.login"))
#         self.assertIsInstance(self.get_context_variable("form"), LoginForm)

#     @patch("app.mail.views.ImapClient")
#     @patch("app.mail.views.current_user")
#     def test_for_redirecting_after_successfull_login(self, user_mock, imap_mock):
#         user_mock.id = 1
#         imap_mock.return_value.state = "AUTH"
#         response = self.client.post(
#             url_for("mail.login"), 
#             data=dict(username="test@gmail.com", password="testowe", 
#                       imap="imap.gmail.com")
#         )
#         self.assertRedirects(response, url_for("mail.client"))

#     @patch("app.mail.views.ImapClient")
#     def test_for_passing_imap_addr_to_imapclient(self, imap_mock):
#         response = self.client.post(
#             url_for("mail.login"), 
#             data=dict(username="test@gmail.com", password="testowe", 
#                       imap="imap.gmail.com")
#         )
#         imap_mock.assert_called_with("imap.gmail.com", timeout=ANY)        

#     @patch("app.mail.views.ImapClient")
#     def test_for_passing_username_and_pass_to_imapclient(self, imap_mock):
#         login_mock = Mock()
#         imap_mock.return_value.login = login_mock

#         response = self.client.post(
#             url_for("mail.login"), 
#             data=dict(username="test@gmail.com", password="testowe", 
#                       imap="imap.gmail.com")
#         )
#         login_mock.assert_called_with("test@gmail.com", "testowe")   

#     @patch("app.mail.views.ImapClient")
#     @patch("app.mail.views.current_user")
#     def test_for_rendering_proper_template_after_login(
#         self, user_mock, imap_mock
#     ):
#         user_mock.id = 1
#         imap_mock.return_value.state = "AUTH"
#         response = self.client.post(
#             url_for("mail.login"), 
#             data=dict(username="test@gmail.com", password="testowe", 
#                       imap="imap.gmail.com"),
#             follow_redirects = True
#         )
#         self.assert_template_used("mail/client.html")


#     @patch("app.mail.views.ImapClient")
#     @patch("app.mail.views.current_user")
#     def test_for_passing_username_to_template(
#         self, user_mock, imap_mock
#     ):
#         user_mock.id = 1
#         imap_mock.return_value.state = "AUTH"
#         imap_mock.return_value.username = "test@gmail.com"
#         response = self.client.post(
#             url_for("mail.login"), 
#             data=dict(username="test@gmail.com", password="testowe", 
#                       imap="imap.gmail.com"),
#             follow_redirects = True
#         )
#         self.assert_context("username", "test@gmail.com")


#     @patch("app.mail.views.ImapClient")
#     @patch("app.mail.views.current_user")
#     def test_for_redirectiong_for_unlogged_users(
#         self, user_mock, imap_mock
#     ):
#         user_mock.id = 5
#         response = self.client.get(url_for("mail.client"))
#         self.assertRedirects(response, url_for("mail.login"))

#     @unittest.skip
#     @patch("app.mail.views.ImapClient")
#     def test_for_saving_imapclient_in_app_context(self, imap_mock):
#         imap_mock.return_value.state = "AUTH"
#         client_mock = Mock()
#         imap_mock.return_value = client_mock

#         response = self.client.post(
#             url_for("mail.login"), 
#             data=dict(username="test@gmail.com", password="testowe", 
#                       imap="imap.gmail.com")
#         )
#         self.assertEqual(g_mock.imap_client, client_mock)