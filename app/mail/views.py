import json
import re
import imaplib
import functools

from flask import (
    render_template, redirect, url_for, request, flash, 
    jsonify, session
)
from flask_login import current_user, login_required

from . import mail
from .forms import LoginForm
from .client import ImapClient, email_to_dict, ImapClientError
from app.utils import utf7_decode

DEFAULT_IDS_FROM = 0
DEFAULT_IDS_TO = 50


@mail.route("/login", methods=["GET", "POST"])
@login_required
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        imap_addr = form.imap.data

        imap_client = None
        try:
            imap_client = ImapClient(imap_addr, timeout = 5) # 5 seconds
        except imaplib.IMAP4.error:
            flash("Unable to connect with service provider. Pleade verify " + 
                  "whether the imap address is correct.")

        if imap_client:
            try:
                imap_client.login(username, password)
            except imaplib.IMAP4.error:
               flash("Invalid username or password.")
                   
            if imap_client.state == "AUTH":      
                session["imap_username"] = username
                session["imap_password"] = password
                return redirect(request.args.get("next") or url_for("mail.client"))

    return render_template("mail/login.html", form=form)

def logout_from_imap():
    session.pop("imap_username", None)
    session.pop("imap_password", None)

@mail.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_from_imap()
    return redirect(url_for("mail.login"))   

################################################################################
# IMAP INTERFACE
################################################################################

def imap_authentication(redirect_to_login=False):
    def decorator(func):
        @functools.wraps(func)
        def authenticate(*args, **kwargs):
            username = session.get("imap_username", None)
            password = session.get("imap_password", None)
            if username and password:
                try:
                    imap_client = ImapClient("imap.gmail.com")
                    imap_client.login(username, password)
                    return func(imap_client)
                except ImapClientError:
                    pass

            if redirect_to_login:
                return redirect(url_for("mail.login"))
            else:     
                response = {"status": "ERROR", "data": "Not authorized access."}
                return jsonify(response)    
        return authenticate
    return decorator


@mail.route("/client", methods=["GET"])
@imap_authentication(redirect_to_login=True)
def client(imap_client):
    return render_template("mail/client.html", 
                           username=imap_client.username)


@mail.route("/list", methods=["GET", "POST"])
@imap_authentication()
def imap_list(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    try:
        status, data = imap_client.list()

        mailboxes = list()
        p = re.compile(r'"(?P<name>[^"]*)"$')
        noselect = re.compile(r'\\noselect', re.IGNORECASE)
        for mailbox in data:
            mailbox = mailbox.decode("ascii")
            if noselect.search(mailbox) is not None:
                continue
            m = p.search(mailbox)
            if m:
                mailboxes.append({
                    "utf7": m.group("name"),
                    "utf16": utf7_decode(m.group("name"))
                })

        return jsonify({"status": "OK", "data": mailboxes})
    except Exception as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})


@mail.route("/get_headers", methods=["GET", "POST"])
@imap_authentication()
def imap_get_headers(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    try:
        status, count = imap_client.len_mailbox(
            '"' + args.get("mailbox", "INBOX") + '"'
        )

        if count > 0:
            ids = range(count, 0, -1) # Create ids of mails
            ids_from = max(int(args.get(
                           "ids_from", DEFAULT_IDS_FROM)), 1) - 1
            ids_to = min(int(args.get(
                         "ids_to", DEFAULT_IDS_TO)), len(ids))

            if ids_from > ids_to:
                status = "ERROR"
                data = "Invalid e-mails' ranges (ids_from <= ids_to)."
            else:
                status, data = imap_client.get_headers(
                    ids[slice(ids_from, ids_to)],
                    fields=["Subject", "Date", "From"]
                )
                data = list(reversed(data))
        else:
            status, data = "OK", [] # Empty mailbox

        response = {"status": status, "data": data, "total_emails": count}
        return jsonify(response)

    except Exception as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})

  
@mail.route("/get_emails", methods=["GET", "POST"])
@imap_authentication()
def imap_get_emails(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    try:
        status_select, _ = imap_client.select(
            args.get("mailbox", "INBOX")
        )

        ids = args.get("ids", None)
        if ids:
            status, data = imap_client.get_emails(ids)

            # Process & decode emails
            emails = list()
            for email in data:
                emails.append(email_to_dict(email))

            response = {"status": "OK", "data": emails}
        else:
            response = {"status": "ERROR", 
                       "data": {"msg": "Unspecified e-mails ids."}}

        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})



@mail.route("/get_email", methods=["GET", "POST"])
@imap_authentication()
def imap_get_email(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    return None