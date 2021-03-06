import unittest
from unittest.mock import patch, Mock, ANY, call
import email
import imaplib

from tests.base import FlaskTestCase
from app.mail.client import (
    ImapClient, email_to_dict, ImapClientError, DEFAULT_MAILBOX,
    process_email_for_display, imaplib_decorator
)

from tests.mail import imap_responses


@patch("app.mail.client.imaplib")
class CSearchTest(unittest.TestCase):

    def mock_socket(self, imap_mock):
        mock = Mock()
        imap_mock.IMAP4_SSL.return_value.socket = mock
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return mock

    def test_for_raising_error_when_criteria_not_sequence(self, imap_mock):
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(TypeError):
            iclient.csearch({"key": "value"}, clear_socket=False)

    def test_for_calling_socket_method(self, imap_mock):
        socket_mock = self.mock_socket(imap_mock)
        socket_mock.return_value.recv.side_effect = [ 
            b'+ go ahead\r\n', 
            b'* SEARCH 3 4\r\nA2444 OK SEARCH completed (Success)\r\n' 
        ]
        iclient = ImapClient("imap.gmail.com")
        iclient.csearch([{"key": "SUBJECT", "value": "Test", "decode": True}], 
                        clear_socket=False)
        self.assertTrue(socket_mock.called)

    def test_calls_socket_send_method_with_proper_args1(self, imap_mock):
        socket_mock = self.mock_socket(imap_mock)
        socket_mock.return_value.recv.side_effect = [ 
            b'+ go ahead\r\n', 
            b'* SEARCH 3 4\r\nA2444 OK SEARCH completed (Success)\r\n' 
        ]
        send_mock = Mock()
        socket_mock.return_value.send = send_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.csearch([{"key": "SUBJECT", "value": "Test", "decode": True}], 
                        clear_socket=False)
        expected = [
            call(send_mock.call_args_list[0][0][0][:5] + # random tag
                 b" SEARCH CHARSET UTF-8 SUBJECT {4}\r\n"), 
            call(b"Test\r\n")
        ]
        self.assertEqual(send_mock.call_count, 2)
        self.assertEqual(send_mock.call_args_list, expected)

    def test_calls_socket_send_method_with_proper_args2(self, imap_mock):
        socket_mock = self.mock_socket(imap_mock)
        socket_mock.return_value.recv.side_effect = [ 
            b'+ go ahead\r\n', 
            b'+ go ahead\r\n', 
            b'* SEARCH 3 4\r\nA2444 OK SEARCH completed (Success)\r\n' 
        ]
        send_mock = Mock()
        socket_mock.return_value.send = send_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.csearch([{"key": "FROM", "value": "JAGO", "decode": True}, 
                         {"key": "SUBJECT", "value": "Test Mail", "decode": True}],
                        clear_socket=False)
        expected = [
            call(send_mock.call_args_list[0][0][0][:5] + # random tag 
                 b" SEARCH CHARSET UTF-8 FROM {4}\r\n"), 
            call(b"JAGO SUBJECT {9}\r\n"),
            call(b"Test Mail\r\n")
        ]
        self.assertEqual(send_mock.call_count, 3)
        self.assertEqual(send_mock.call_args_list, expected)

    def test_returns_status_and_data(self, imap_mock):
        socket_mock = self.mock_socket(imap_mock)
        socket_mock.return_value.recv.side_effect = [ 
            b'+ go ahead\r\n', 
            b'+ go ahead\r\n', 
            b'* SEARCH 3 4\r\nA2444 OK SEARCH completed (Success)\r\n' 
        ]
        send_mock = Mock()
        socket_mock.return_value.send = send_mock
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.csearch([
                            {"key": "FROM", "value": "JAGO", "decode": True}, 
                            {"key": "SUBJECT", "value": "Test Mail", "decode": True}
                        ], clear_socket=False)
        self.assertEqual(status, "OK")
        self.assertEqual(set(data), set([3, 4]))

    def test_returns_status_and_msg_when_bad_or_error(self, imap_mock):
        socket_mock = self.mock_socket(imap_mock)
        socket_mock.return_value.recv.side_effect = [ 
            b'+ go ahead\r\n', 
            b'+ go ahead\r\n', 
            b'A2444 BAD Could not parse command\r\n'
        ]
        send_mock = Mock()
        socket_mock.return_value.send = send_mock
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.csearch([
                            {"key": "FROM", "value": "JAGO", "decode": True}, 
                            {"key": "SUBJECT", "value": "Test Mail", "decode": True}
                        ], clear_socket=False)
        self.assertEqual(status, "BAD")
        self.assertEqual(data, 'A2444 BAD Could not parse command')

    def test_raises_error_when_invalid_criterion(self, imap_mock):
        socket_mock = self.mock_socket(imap_mock)
        socket_mock.return_value.recv.side_effect = [ 
            b'+ go ahead\r\n', 
            b'+ go ahead\r\n', 
            b'A2444 BAD Could not parse command\r\n'
        ]
        send_mock = Mock()
        socket_mock.return_value.send = send_mock
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.csearch([
                    {"key": "FROM", "decode": True}, 
                    {"key": "SUBJECT", "value": "Test Mail", "decode": True}
                ], clear_socket=False)
            

@patch("app.mail.client.imaplib")
class ManagingMailboxesTest(unittest.TestCase):

    def mock_mtriad(self, imap_mock, response = ('OK', [b'Success'])):
        mocks = list()
        for method in ("create", "delete", "rename"):
            mock = Mock()
            mock.return_value = response
            setattr(ImapClient, method, imaplib_decorator()(mock))
            mocks.append(mock)
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return tuple(mocks)

    def test_create_calls_underlying_rename_method(self, imap_mock):
        create_mock, *_ = self.mock_mtriad(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.create("TESST")
        self.assertTrue(create_mock.called)

    def test_delete_calls_underlying_rename_method(self, imap_mock):
        _, delete_mock, _ = self.mock_mtriad(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.delete("TESST")
        self.assertTrue(delete_mock.called)

    def test_rename_calls_underlying_rename_method(self, imap_mock):
        *_, rename_mock = self.mock_mtriad(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.rename("TESST", "TEST")
        self.assertTrue(rename_mock.called)

    def test_create_passes_arguments_to_underlygin_method(self, imap_mock):
        create_mock, *_ = self.mock_mtriad(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.create("TESST")
        create_mock.assert_called_with(iclient, "TESST")  
        
    def test_create_raises_error_when_exception(self, imap_mock):
        create_mock, *_ = self.mock_mtriad(imap_mock)
        create_mock.side_effect = imaplib.IMAP4_SSL.error
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.create("TESST")

    def test_create_raises_error_when_no_response(self, imap_mock):
        create_mock, *_ = self.mock_mtriad(imap_mock, response=("NO", [b"FUCK"]))
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.create("TESST")


@patch("app.mail.client.imaplib")
class StoreTest(unittest.TestCase):

    def mock_store(self, imap_mock, response):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.store = mock_
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return mock_

    def test_for_calling_store_method(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        iclient = ImapClient("imap.gmail.com")
        iclient.store(b'1', "INBOX", command="+FLAGS")
        self.assertTrue(store_mock.called)

    def test_for_passing_arguments_to_store_method(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        iclient = ImapClient("imap.gmail.com")
        iclient.store(b'1', "INBOX", command="+FLAGS")
        store_mock.assert_called_with(b'1', "+FLAGS", "INBOX")   

    def test_returns_ok_status_when_success(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.store(b'1', "INBOX", command="+FLAGS")
        self.assertEqual(status, "OK")

    def test_raises_error_when_failure(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store2)
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.store(b'1', "INBOX", command="+FLAGS")

    def test_raises_error_when_store_exception(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        store_mock.side_effect = imaplib.IMAP4.error
        iclient = ImapClient("imap.gmail.com")      
        with self.assertRaises(ImapClientError):
            iclient.store(b'1', "INBOX", command="+FLAGS")  

    def test_accepts_list_of_ids(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.store([1, 2, 3], "INBOX", command="+FLAGS")
        store_mock.assert_called_with(b'1,2,3', "+FLAGS", "INBOX")

    def test_accepts_single_id(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.store(b'1', "INBOX", command="+FLAGS")
        store_mock.assert_called_with(b'1', "+FLAGS", "INBOX")   

    def test_calls_uid_method_when_uid_set(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        uid_mock = Mock()
        uid_mock.return_value = imap_responses.store
        imap_mock.IMAP4_SSL.return_value.uid = uid_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.store(b'1', "INBOX", command="+FLAGS", uid=True)
        self.assertFalse(store_mock.called)     
        self.assertTrue(uid_mock.called)

    def test_accepts_flags_as_iterable(self, imap_mock):
        store_mock = self.mock_store(imap_mock, imap_responses.store)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.store(b'1', ["\\Flagged", "\\Seen"], 
                                     command="+FLAGS")
        store_mock.assert_called_with(b'1', "+FLAGS", "\\Flagged \\Seen") 


@patch("app.mail.client.imaplib")
class MoveTest(unittest.TestCase):

    def mock_move(self, imap_mock, response):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.copy = mock_
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return mock_

    def test_calls_move_method(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        iclient = ImapClient("imap.gmail.com")
        iclient.move_emails(b'1', "INBOX")
        self.assertTrue(move_mock.called)

    def test_for_passing_args_to_move_method(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        iclient = ImapClient("imap.gmail.com")
        iclient.move_emails(b'1', "INBOX")
        move_mock.assert_called_with(b'1', "INBOX")

    def test_returns_ok_status_when_success(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.move_emails(b'1', "INBOX")
        self.assertEqual(status, "OK")

    def test_raises_error_when_failure(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy2)
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.move_emails(b'1', "INBOX")    

    def test_raises_error_when_imaplib_exception(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy2)
        iclient = ImapClient("imap.gmail.com")
        move_mock.side_effect = imaplib.IMAP4.error
        with self.assertRaises(ImapClientError):
            iclient.move_emails(b'1', "INBOX")  

    def test_accepts_list_of_ids(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        iclient = ImapClient("imap.gmail.com")
        iclient.move_emails([1, 2, 3], "INBOX")  
        move_mock.assert_called_with(b'1,2,3', "INBOX")

    def test_accepts_string_of_ids(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        iclient = ImapClient("imap.gmail.com")
        iclient.move_emails("1, 2, 3", "INBOX")  
        move_mock.assert_called_with(b'1,2,3', "INBOX")

    def test_accepts_single_id(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        iclient = ImapClient("imap.gmail.com")
        iclient.move_emails(3, "INBOX")  
        move_mock.assert_called_with(b'3', "INBOX")

    def test_calls_uid_method_when_uid_set(self, imap_mock):
        move_mock = self.mock_move(imap_mock, imap_responses.copy)
        uid_mock = Mock()
        uid_mock.return_value = imap_responses.copy
        imap_mock.IMAP4_SSL.return_value.uid = uid_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.move_emails(b'1', "INBOX", uid=True)
        self.assertFalse(move_mock.called)     
        self.assertTrue(uid_mock.called)


@patch("app.mail.client.imaplib")
class LoginTest(unittest.TestCase):

    def mock_login(self, imap_mock, response = ("OK", [b'msg'])):
        mock = Mock()
        mock.return_value = response
        imap_mock.IMAP4_SSL.return_value.login = mock
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return mock

    def test_saves_useranme(self, imap_mock):
        self.mock_login(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.login("Kuba", "Kuba")
        self.assertEqual(iclient.username, "Kuba")

    def test_raises_imapclienterror_when_impalib_error(self, imap_mock):
        login_mock = self.mock_login(imap_mock)
        login_mock.side_effect = imaplib.IMAP4.error
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.login("Kuba", "Kuba")

    def test_raises_imapclienterror_when_status_error(self, imap_mock):
        self.mock_login(imap_mock, response=("ERROR", [b'NO LOGIN']))
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.login("Kuba", "Kuba")   

@patch("app.mail.client.imaplib")
class SelectTest(unittest.TestCase):

    def mock_select(self, imap_mock, response = ("OK", [b'msg'])):
        mock = Mock()
        mock.return_value = response
        imap_mock.IMAP4_SSL.return_value.select = mock
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return mock

    def test_calls_imaplib_login_method(self, imap_mock):
        select_mock = self.mock_select(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.select()
        self.assertTrue(select_mock.called)       

    def test_saves_mailbox(self, imap_mock):
        self.mock_select(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.select("JEDEN")
        self.assertEqual(iclient.mailbox, "JEDEN")

    def test_accepts_default_mailbox(self, imap_mock):
        self.mock_select(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.select()
        self.assertEqual(iclient.mailbox, DEFAULT_MAILBOX)       

    def test_raises_imapclienterror_when_impalib_error(self, imap_mock):
        select_mock = self.mock_select(imap_mock)
        select_mock.side_effect = imaplib.IMAP4.error
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.select()

    def test_raises_imapclienterror_when_status_error(self, imap_mock):
        select_mock = self.mock_select(imap_mock, 
                                       response=("ERROR", [b'NO LOGIN']))
        select_mock.side_effect = imaplib.IMAP4.error
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.select()      


@patch("app.mail.client.imaplib")
class ListTest(unittest.TestCase):

    def mock_list(self, imap_mock, response = ("OK", [b'msg'])):
        mock = Mock()
        mock.return_value = response
        imap_mock.IMAP4_SSL.return_value.list = mock
        imap_mock.IMAP4.error = imaplib.IMAP4.error
        return mock

    def test_calls_imaplib_list_method(self, imap_mock):
        list_mock = self.mock_list(imap_mock, response=imap_responses.list2)
        iclient = ImapClient("imap.gmail.com")
        iclient.list()
        self.assertTrue(list_mock.called)       

    def test_raises_imapclienterror_when_impalib_error(self, imap_mock):
        list_mock = self.mock_list(imap_mock)
        list_mock.side_effect = imaplib.IMAP4.error
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.list()

    def test_raises_imapclienterror_when_status_error(self, imap_mock):
        list_mock = self.mock_list(imap_mock, 
                                   response=("ERROR", [b'NO LOGIN']))
        list_mock.side_effect = imaplib.IMAP4.error
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.list()   

    def test_returns_status_and_list_with_tuples(self, imap_mock):
        list_mock = self.mock_list(imap_mock, response=imap_responses.list2)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.list()  
        self.assertEqual(status, "OK")
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 9)
        self.assertIsInstance(data[0], tuple)

    def test_returns_names_of_mailboxes(self, imap_mock):
        list_mock = self.mock_list(imap_mock, response=imap_responses.list2)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.list()      
        names = [ name for name, *_ in data]   
        self.assertIn("INBOX", names)
        self.assertIn("[Gmail]/Sent Mail", names)

    def test_returns_additional_attributes(self, imap_mock):
        list_mock = self.mock_list(imap_mock, response=imap_responses.list2)
        iclient = ImapClient("imap.gmail.com")
        status, data = iclient.list()              
        mailboxes = { name: attrs for name, attrs, *_ in data }
        self.assertIn("\\Noselect", mailboxes["[Gmail]"])
        self.assertIn("\\All", mailboxes["[Gmail]/All Mail"])
        self.assertIn("\\Drafts", mailboxes["[Gmail]/Drafts"])
        self.assertIn("\\Flagged", mailboxes["[Gmail]/Starred"])
        self.assertIn("\\Junk", mailboxes["[Gmail]/Spam"])
        self.assertIn("\\Sent", mailboxes["[Gmail]/Sent Mail"])
        self.assertIn("\\Trash", mailboxes["[Gmail]/Trash"])


class EmailToDictTest(unittest.TestCase):

    def setUp(self):
        self.email_multipart_1 = email.message_from_string('MIME-Version: 1.0\nReceived: by 10.31.193.72 with HTTP; Thu, 24 Nov 2016 12:40:14 -0800 (PST)\nDate: Thu, 24 Nov 2016 21:40:14 +0100\nDelivered-To: jago.eboard@gmail.com\nMessage-ID: <CAB9kREyhEQbZr+KucZwPebH7H9Jpmy8x250XExgRu6s9dwmnnw@mail.gmail.com>\nSubject: Test\nFrom: Jago Eboard <jago.eboard@gmail.com>\nTo: jago.eboard@gmail.com\nContent-Type: multipart/alternative; boundary=001a114e019a3537940542120390\n\n--001a114e019a3537940542120390\nContent-Type: text/plain; charset=UTF-8\n\nE-Mail Testowy\n\n--001a114e019a3537940542120390\nContent-Type: text/html; charset=UTF-8\n\n<div dir="ltr">E-Mail Testowy<br></div>\n\n--001a114e019a3537940542120390--\n')

        self.email_text_1 = email.message_from_string('MIME-Version: 1.0\nReceived: by 10.31.193.72 with HTTP; Thu, 24 Nov 2016 12:40:14 -0800 (PST)\nDate: Thu, 24 Nov 2016 21:40:14 +0100\nDelivered-To: jago.eboard@gmail.com\nMessage-ID: <CAB9kREyhEQbZr+KucZwPebH7H9Jpmy8x250XExgRu6s9dwmnnw@mail.gmail.com>\nSubject: Test\nFrom: Jago Eboard <jago.eboard@gmail.com>\nTo: jago.eboard@gmail.com\nContent-Type: text/plain; charset=UTF-8\n\nE-Mail Testowy\n')

    def test_returns_dictionary(self):
        result = email_to_dict(self.email_multipart_1)
        self.assertIsInstance(result, dict)

    def test_returns_dict_with_header_and_body_keys(self):
        result = email_to_dict(self.email_multipart_1)
        self.assertIn("header", result)
        self.assertIn("body", result)

    def test_header_contains_fields_from_email(self):
        result = email_to_dict(self.email_multipart_1)
        self.assertIn("MIME-Version", result["header"])
        self.assertIn("Date", result["header"])
        self.assertIn("Subject", result["header"])

    def test_returns_body_as_list_when_multipart(self):
        result = email_to_dict(self.email_multipart_1)
        self.assertIsInstance(result["body"], list)

    def test_returns_body_as_str_when_not_multipart(self):
        result = email_to_dict(self.email_text_1)
        self.assertIsInstance(result["body"], str)

    def test_returns_list_with_proper_number_of_items(self):
        result = email_to_dict(self.email_multipart_1)
        self.assertEqual(len(result["body"]), 2)

    def test_items_in_list_contains_body_and_header_fields(self):
        result = email_to_dict(self.email_multipart_1)
        self.assertIn("header", result["body"][0])
        self.assertIn("body", result["body"][0])

@patch("app.mail.client.imaplib")
class GetEmailsTest(FlaskTestCase):

    def mock_fetch(self, imap_mock, response = imap_responses.get_emails):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.fetch = mock_
        return mock_

    def test_calls_fetch_method(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.get_emails(b'1')
        self.assertTrue(fetch_mock.called)

    def test_returns_list_of_message_objects(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, emails = iclient.get_emails(b'1, 2')
        self.assertEqual(len(emails), 2)
        self.assertIsInstance(emails[0], email.message.Message)

    def test_passess_ids_to_fetch_method(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, emails = iclient.get_emails(b'1, 2, 3')
        fetch_mock.assert_called_with(b'1, 2, 3', ANY)

    def test_accepts_list_of_ids(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, emails = iclient.get_emails([1, 2, 3])
        fetch_mock.assert_called_with(b'1,2,3', ANY)

    def test_accepts_string_of_ids(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, emails = iclient.get_emails("1, 2, 3")
        fetch_mock.assert_called_with(b'1,2,3', ANY)

    def test_accepts_single_id(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, emails = iclient.get_emails(1)
        fetch_mock.assert_called_with(b'1', ANY)

    def test_calls_uid_method_when_uid_set(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        uid_mock = Mock()
        uid_mock.return_value = imap_responses.fetch
        imap_mock.IMAP4_SSL.return_value.uid = uid_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.get_emails(b'2043', uid=True)
        self.assertFalse(fetch_mock.called)     
        self.assertTrue(uid_mock.called)

@patch("app.mail.client.imaplib")
class GetHeadersTest(FlaskTestCase):

    def mock_fetch(self, imap_mock, response = imap_responses.get_headers):
        mock_ = Mock()
        mock_.return_value = response
        imap_mock.IMAP4_SSL.return_value.fetch = mock_
        return mock_

    def test_calls_fetch_method(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        iclient.get_headers(b'1', sort_by_date=False)
        self.assertTrue(fetch_mock.called)

    def test_returns_list_of_dicts_with_fields_as_keys(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers(b'1', fields=["Subject", "From"],
                                             sort_by_date=False)
        self.assertTrue(isinstance(header, list))
        self.assertIn("Subject", header[0])
        self.assertIn("From", header[0])

    def test_check_for_proper_data_in_header(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers(b'1', fields=["Subject", "From"],
                                             sort_by_date=False)
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
        status, header = iclient.get_headers(b'1', fields = ["Subject", "From"])
        self.assertEqual(len(header), 2)

    def test_passess_ids_to_fetch_method(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers(b'1, 2, 3', fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1, 2, 3', ANY)

    def test_accepts_list_of_ids(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers([1, 2, 3], fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1,2,3', ANY)

    def test_accepts_string_of_ids(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers("1, 2, 3", fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1,2,3', ANY)

    def test_accepts_single_id(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch2)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers(1, fields = ["Subject", "From"])
        fetch_mock.assert_called_with(b'1', ANY)

    def test_returns_id_of_the_message(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers(b'2043', fields = ["Subject", "From"])
        self.assertEqual(header[0]["id"], 2043)

    def test_passes_fields_to_fetch(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch)
        iclient = ImapClient("imap.gmail.com")
        status, header = iclient.get_headers(b'2043', fields = ["Subject", "From"])[0]
        self.assertIn("Subject", fetch_mock.call_args[0][1])
        self.assertIn("From", fetch_mock.call_args[0][1])
        self.assertNotIn("Date", fetch_mock.call_args[0][1])

    def test_calls_uid_method_when_uid_set(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, response = imap_responses.fetch)
        uid_mock = Mock()
        uid_mock.return_value = imap_responses.fetch
        imap_mock.IMAP4_SSL.return_value.uid = uid_mock
        iclient = ImapClient("imap.gmail.com")
        iclient.get_headers(b'2043', uid=True)
        self.assertFalse(fetch_mock.called)     
        self.assertTrue(uid_mock.called)

    def test_returns_list_with_flags_for_each_email(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, imap_responses.fetch3)
        iclient = ImapClient("imap.gmail.com")
        header, header = iclient.get_headers(b'9', flags=True)
        self.assertIn("Flags", header[0])
        self.assertTrue(isinstance(header[0]["Flags"], list))

    def test_accepts_flags_argument(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, imap_responses.fetch3)
        iclient = ImapClient("imap.gmail.com")
        iclient.get_headers(b'2043', flags=True)

    def test_calls_fetch_with_FLAGS_part(self, imap_mock):
        fetch_mock = self.mock_fetch(imap_mock, imap_responses.fetch3)
        iclient = ImapClient("imap.gmail.com")
        iclient.get_headers(b'9', flags=True)
        self.assertIn("FLAGS", fetch_mock.call_args[0][1])

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
        mail_mock.return_value = ("OK", [b'msg'])
        imap_mock.IMAP4_SSL.return_value.login = mail_mock
        imap_mock.IMAP4.error = imaplib.IMAP4.error
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
        with self.assertRaises(ImapClientError):
            iclient.list_mailbox()       

    def test_list_mailbox_returns_select_error(self, imap_mock):
        self.mock_select(imap_mock, ("NO", b"Failure"))
        search_mock = self.mock_search(imap_mock)
        # imap_mock.IMAP4_SSL.return_value.search = search_mock        
        iclient = ImapClient("imap.gmail.com")
        with self.assertRaises(ImapClientError):
            iclient.list_mailbox()

    def test_list_mailbox_returns_list_of_mails_ids(self, imap_mock):
        self.mock_select(imap_mock)
        self.mock_search(imap_mock)
        iclient = ImapClient("imap.gmail.com")
        status, mails_ids = iclient.list_mailbox()
        self.assertEqual(status, "OK")
        self.assertEqual(mails_ids, [1, 2, 3, 4, 5])
        


class ProcessEmailForDisplayTest(unittest.TestCase):

    def setUp(self):
        self.email_multipart_1 = email.message_from_string('MIME-Version: 1.0\nReceived: by 10.31.193.72 with HTTP; Thu, 24 Nov 2016 12:40:14 -0800 (PST)\nDate: Thu, 24 Nov 2016 21:40:14 +0100\nDelivered-To: jago.eboard@gmail.com\nMessage-ID: <CAB9kREyhEQbZr+KucZwPebH7H9Jpmy8x250XExgRu6s9dwmnnw@mail.gmail.com>\nSubject: Test\nFrom: Jago Eboard <jago.eboard@gmail.com>\nTo: jago.eboard@gmail.com\nContent-Type: multipart/alternative; boundary=001a114e019a3537940542120390\n\n--001a114e019a3537940542120390\nContent-Type: text/plain; charset=UTF-8\n\nE-Mail Testowy\n\n--001a114e019a3537940542120390\nContent-Type: text/html; charset=UTF-8\n\n<div dir="ltr">E-Mail Testowy<br></div>\n\n--001a114e019a3537940542120390--\n')

        self.email_text_1 = email.message_from_string('MIME-Version: 1.0\nReceived: by 10.31.193.72 with HTTP; Thu, 24 Nov 2016 12:40:14 -0800 (PST)\nDate: Thu, 24 Nov 2016 21:40:14 +0100\nDelivered-To: jago.eboard@gmail.com\nMessage-ID: <CAB9kREyhEQbZr+KucZwPebH7H9Jpmy8x250XExgRu6s9dwmnnw@mail.gmail.com>\nSubject: Test\nFrom: Jago Eboard <jago.eboard@gmail.com>\nTo: jago.eboard@gmail.com\nContent-Type: text/plain; charset=UTF-8\n\nE-Mail Testowy\n')

    def test_returns_dictionary(self):
        result = process_email_for_display(self.email_multipart_1)
        self.assertIsInstance(result, dict)

    def test_returns_type_node_when_multipart(self):
        result = process_email_for_display(self.email_multipart_1)
        self.assertEqual(result["type"], "node")

    def test_returns_list_as_content_when_multipart(self):
        result = process_email_for_display(self.email_multipart_1)
        self.assertIsInstance(result["content"], list)

    def test_returns_type_content_when_text(self):
        result = process_email_for_display(self.email_text_1)
        self.assertEqual(result["type"], "plain")

    # def test_returns_str_in_body_when_plan_text(self):
    #     result = process_email_for_display(self.email_text_1)
    #     self.assertIsInstance(result["body"], str)        