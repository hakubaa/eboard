import unittest
from unittest.mock import patch, Mock, ANY

from tests.base import FlaskTestCase
from app.mail.client import ImapClient
from tests import imap_responses


@patch("app.mail.client.imaplib")
class GetHeaderTest(FlaskTestCase):

    def mock_fetch(self, imap_mock, response = imap_responses.fetch):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.fetch = mock_
        return mock_

    def test_calls_fetch_method(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.get_header(b'1')
        self.assertTrue(fetch_mock.called)

    def test_returns_list_of_dicts_with_fields_as_keys(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(b'1', fields = ["Subject", "From"])
        self.assertTrue(isinstance(header, list))
        self.assertIn("Subject", header[0])
        self.assertIn("From", header[0])

    def test_check_for_proper_data_in_header(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(b'1', fields = ["Subject", "From"])
        self.assertTrue(
            header[0]["Subject"],
            "New on CodinGame: Check it out!"
        )     
        self.assertTrue(
            header[0]["From"],
            "CodinGame <coders@codingame.com>"
        )

    def test_returns_headers_of_many_messages(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(b'1', fields = ["Subject", "From"])
        self.assertEqual(len(header), 2)

    def test_passess_ids_to_fetch_method(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(b'1, 2, 3', fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1, 2, 3', ANY)

    def test_accepts_list_of_ids(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header([1, 2, 3], fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1,2,3', ANY)

    def test_accepts_string_of_ids(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header("1, 2, 3", fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1, 2, 3', ANY)

    def test_accepts_single_id(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(1, fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1', ANY)

    def test_returns_id_of_the_message(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(b'2043', fields = ["Subject", "From"])
        self.assertEqual(header[0]["id"], 2043)

    def test_passes_fields_to_fetch(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_header(b'2043', fields = ["Subject", "From"])[0]
        self.assertIn("Subject", fetch_mock.call_args[0][1])
        self.assertIn("From", fetch_mock.call_args[0][1])
        self.assertNotIn("Date", fetch_mock.call_args[0][1])

    def test_calls_uid_method_when_uid_set(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch)
        uid_mock = Mock()
        uid_mock.return_value = imap_responses.fetch
        imap_mock.IMAP4_SSL.return_value.uid = uid_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.get_header(b'2043', uid=True)
        self.assertFalse(fetch_mock.called)     
        self.assertTrue(uid_mock.called)



@patch("app.mail.client.imaplib")
class ListMailboxTest(FlaskTestCase):

    def mock_select(self, imap_mock, response = ("OK", b"2044")):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.select = mock_
        return mock_

    def mock_search(self, imap_mock, 
                    response = ('OK', [b'1 2 3 4 5'])):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.search = mock_
        return mock_

    def test_init_accepts_addr(self, imap_mock):
        iclient = ImapClient("imap.gmail.com")
    
    def test_init_passes_addr_to_imap(self, imap_mock):
        imap_mock.IMAP4_SSL = Mock()
        iclient = ImapClient("imap.gmail.com")
        imap_mock.IMAP4_SSL.assert_called_with("imap.gmail.com")

    def test_init_saves_imap_object_in_mail(self, imap_mock):
        test_mock = Mock()
        imap_mock.IMAP4_SSL.return_value = test_mock
        iclient = ImapClient("imap.gmail.com")
        self.assertIs(iclient.mail, test_mock)

    def test_login_passes_email_and_username_to_imap_login(self, imap_mock):
        mail_mock = Mock()
        imap_mock.IMAP4_SSL.return_value.login = mail_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.login("test@gmail.com", "testowe")
        mail_mock.assert_called_with("test@gmail.com", "testowe")

    def test_for_delagating_to_imap_instance(self, imap_mock):
        method_mock = Mock()
        imap_mock.IMAP4_SSL.return_value.method2mock = method_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.method2mock("IMAP")
        method_mock.assert_called_with("IMAP")

    def test_list_mailbox_selects_the_proper_mailbox(self, imap_mock):
        select_mock = self.mock_select(imap_mock)
        self.mock_search(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.list_mailbox("IMPORTANT")
        select_mock.assert_called_with("IMPORTANT")

    def test_list_mailbox_set_default_mailbox(self, imap_mock):
        select_mock = self.mock_select(imap_mock)
        self.mock_search(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.list_mailbox()
        select_mock.assert_called_with("INBOX")   

    def test_list_mailbox_accepts_uid_as_optional_named_parameter(self, imap_mock):
        self.mock_select(imap_mock)
        self.mock_search(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.list_mailbox("IMPORTANT", uid = False)

    def test_list_mailbox_calls_search_with_ALL_by_default(self, imap_mock):
        self.mock_select(imap_mock)
        search_mock = self.mock_search(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.list_mailbox()
        search_mock.assert_called_with(None, "ALL")

    def test_list_mailbox_propagates_search_criteria(self, imap_mock):
        self.mock_select(imap_mock)
        search_mock = self.mock_search(imap_mock)
        # imap_mock.IMAP4_SSL.return_value.search = search_mock
        iclient = ImapClient("imap.gmail.com")
        criteria = '(FROM "Doug" SUBJECT "test message 2")'
        iclient.list_mailbox("INBOX", criteria)
        search_mock.assert_called_with(None, criteria)

    def test_list_mailbox_does_not_call_search_when_select_error(
        self, imap_mock
    ):
        self.mock_select(imap_mock, ("NO", b"Failure"))
        search_mock = self.mock_search(imap_mock)
        # imap_mock.IMAP4_SSL.return_value.search = search_mock        
        iclient = ImapClient("imap.gmail.com")
        iclient.list_mailbox()       
        self.assertFalse(search_mock.called)

    def test_list_mailbox_returns_select_error(self, imap_mock):
        self.mock_select(imap_mock, ("NO", b"Failure"))
        search_mock = self.mock_search(imap_mock)
        # imap_mock.IMAP4_SSL.return_value.search = search_mock        
        iclient = ImapClient("imap.gmail.com")
        self.assertEqual(iclient.list_mailbox(), ("NO", b"Failure"))

    def test_list_mailbox_returns_list_of_mails_ids(self, imap_mock):
        self.mock_select(imap_mock)
        self.mock_search(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, mails_ids = iclient.list_mailbox()
        self.assertEqual(status, "OK")
        self.assertEqual(mails_ids, [b'1', b'2', b'3', b'4', b'5'])
        


# import unittest
# from unittest.mock import patch, Mock
# import imaplib

# from tests.base import FlaskTestCase
# from app.mail.client import ImapClient


# @patch("app.mail.client.imaplib")
# class MailClientTest(FlaskTestCase):

#     def test_init_accepts_addr(self, imap_mock):
#         iclient = ImapClient("imap.gmail.com")
    
#     def test_client_inhertis_from_imap(self, imap_mock):
#         self.assertIn(imaplib.IMAP4_SSL, ImapClient.__bases__)

#     def test_list_mailbox_selects_the_proper_mailbox(self, imap_mock):
#         select_mock = Mock()
#         imap_mock.IMAP4_SSL.return_value.select = select_mock
#         iclient = ImapClient("imap.gmail.com")
#         iclient.list_mailbox("IMPORTANT")
#         select_mock.assert_called_with("IMPORTANT")

#     def test_list_mailbox_returns_list_of_mail(self, imap_mock):
#         pass