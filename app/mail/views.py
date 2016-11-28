import json
import re
import imaplib

from flask import (
    render_template, redirect, url_for, request, flash, g,
    jsonify
)
from flask_login import current_user, login_required

from . import mail
from .forms import LoginForm
from .client import ImapClient, email_to_dict


DEFAULT_IDS_FROM = 0
DEFAULT_IDS_TO = 50


# check timestamps (compare client creation with current time)
imap_clients = dict()


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
                g.imap_client = imap_client    
                imap_clients[current_user.id] = imap_client
                return redirect(request.args.get("next") or url_for("mail.client"))

    return render_template("mail/login.html", form=form)


@mail.route("/client", methods=["GET"])
@login_required
def client():
    imap_client = imap_clients.get(current_user.id, None)
    if imap_client:
        return render_template("mail/client.html")
    return redirect(url_for("mail.login"))


@mail.route("/list", methods=["GET", "POST"])
def imap_list():
    imap_client = imap_clients.get(current_user.id, None)
    if imap_client:
        try:
            status, data = imap_client.list()
        except imaplib.IMAP4.error:
            status = "ERROR"

        if status == "OK":
            mailboxes = list()
            p = re.compile('"(?P<name>[^" ]*)"$')
            for mailbox in data:
                m = p.search(mailbox.decode())
                if m:
                    mailboxes.append(m.group("name"))
            response = {
                "status": "OK",
                "data": mailboxes
            }
        else:
            response = {
                "status": "ERROR",
                "data": {"msg": "Unable to get list of mailboxes."}
            }
    else:
        response = { 
            "status": "ERROR", 
            "data": {"msg": "Not authorized access."} 
        }
    return jsonify(response)


@mail.route("/get_headers", methods=["GET", "POST"])
def imap_get_headers():
    imap_client = imap_clients.get(current_user.id, None)
    if imap_client:
        try:
            status, count = imap_client.len_mailbox(
                request.args.get("mailbox", "INBOX")
            )
        except imaplib.IMAP4.error:
            status = "ERROR"

        if status == "OK":
            if count > 0:
                ids = range(count, 0, -1) # Create ids of mails
                ids_from = max(int(request.args.get(
                               "ids_from", DEFAULT_IDS_FROM)), 0)
                ids_to = min(int(request.args.get(
                             "ids_to", DEFAULT_IDS_TO)), len(ids))

                if ids_from >= ids_to:
                    status = "ERROR"
                    msg = "Invalid e-mails' ranges (ids_from <= ids_to)."
                else:
                    try:
                        status, data = imap_client.get_headers(
                            ids[slice(ids_from, ids_to)],
                            fields=["Subject", "Date", "From"]
                        )
                    except imaplib.IMAP4.error:
                        status = "ERROR"

                    if status != "OK":
                        msg = "Unable to get e-mails' headers."
            else:
                status, data = "OK", [] # Empty mailbox

            if status == "OK":
                response = {
                    "status": status,
                    "data": list(reversed(data))
                }
                return jsonify(response)
        else:
            msg = "Unable to get list of e-mails."
    else:
        msg = "Not authorized access."

    response = {
        "status": "ERROR",
        "data": msg
    }
    return jsonify(response)


@mail.route("/get_emails", methods=["GET", "POST"])
def imap_get_emails():
    imap_client = imap_clients.get(current_user.id, None)

    if imap_client:

        try:
            status_select, _ = imap_client.select(
                request.args.get("mailbox", "INBOX")
            )
        except imaplib.IMAP4.error:
            status_select = "ERROR"

        if status_select == "OK":
            ids = request.args.get("ids", None)
            if ids:
                try:
                    status, data = imap_client.get_emails(ids)
                except imaplib.IMAP4.error:
                    status = "ERROR"

                if status == "OK":
                    # Process & decode emails
                    emails = list()

                    for email in data:
                        emails.append(email_to_dict(email))

                    response = {
                        "status": "OK",
                        "data": emails
                    }
                    return jsonify(response)
                else:
                    msg = "Unable to read emails."
            else:
                msg = "Unspecified e-mails ids."
        else:
            msg = "Unable to select mailbox."
    else:
        msg = "Not authorized access."
         
    response = {
        "status": "ERROR",
        "data": msg
    }
    return jsonify(response)