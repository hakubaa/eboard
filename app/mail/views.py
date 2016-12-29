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
from .client import (
    ImapClient, email_to_dict, ImapClientError, process_email_for_display
)
from app.utils import utf7_decode, utf7_encode

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
            except ImapClientError:
               flash("Invalid username or password.")
                   
            if imap_client.state == "AUTH":      
                session["imap_username"] = username
                session["imap_password"] = password
                session["imap_addr"] = imap_addr
                return redirect(request.args.get("next") or url_for("mail.client"))

    return render_template("mail/login.html", form=form)

def logout_from_imap():
    session.pop("imap_username", None)
    session.pop("imap_password", None)
    session.pop("imap_addr", None)

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
            imap_addr = session.get("imap_addr", None)
            if username and password:
                try:
                    imap_client = ImapClient(imap_addr)
                    imap_client.login(username, password)
                    return func(imap_client, *args, **kwargs)
                except ImapClientError:
                    pass

            if redirect_to_login:
                return redirect(url_for("mail.login"))
            else:     
                response = {"status": "ERROR", "data": "Not authorized access."}
                return jsonify(response)    
        return authenticate
    return decorator

def adjust_mailbox(mailbox):
    return '"' + mailbox + '"'

@mail.route("/client", methods=["GET"])
@imap_authentication(redirect_to_login=True)
def client(imap_client):
    return render_template("mail/client.html", 
                           username=imap_client.username)


@mail.route("/list", methods=["GET", "POST"])
@imap_authentication()
def imap_list(imap_client):
    try:
        status, data = imap_client.list()
        mailboxes = list()
        for name, flags in data:
            mailboxes.append({
                "utf7": name,
                "utf16": utf7_decode(name),
                "flags": flags
            })
        return jsonify({"status": "OK", "data": mailboxes})
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})


@mail.route("/get_headers", methods=["GET", "POST"])
@imap_authentication()
def imap_get_headers(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox name."}})

    if "ids" not in args and ("ids_from" not in args or "ids_to" not in args):
        return jsonify({"status": "ERROR", 
                        "`data": {"msg": "Undefined mailbox name."}})

    try:
        status, count = imap_client.len_mailbox(
            adjust_mailbox(args.get("mailbox", "INBOX"))
        )
        if count > 0:
            if "ids" in args:
                ids = args["ids"]
            else:
                ids = range(count, 0, -1) # Create ids of mails
                ids_from = max(int(args.get(
                               "ids_from", DEFAULT_IDS_FROM)), 1) - 1
                ids_to = min(int(args.get(
                             "ids_to", DEFAULT_IDS_TO)), len(ids))

                if ids_from > ids_to:
                    raise ImapClientError("Invalid e-mails' ranges " +
                                          "(ids_from > ids_to).")

                ids = ids[slice(ids_from, ids_to)]

            status, data = imap_client.get_headers(
                ids,
                fields=["Subject", "Date", "From", "Content-Type"],
                sort_by_date=False
            )
            data = list(reversed(data))
        else:
            status, data = "OK", [] # Empty mailbox

        response = {"status": status, "data": data, "total_emails": count}
        return jsonify(response)

    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})

  
@mail.route("/get_raw_emails", methods=["GET", "POST"])
@imap_authentication()
def imap_get_raw_emails(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    try:
        ids = args.get("ids", None)
        if ids:
            status_select, _ = imap_client.select(
                adjust_mailbox(args.get("mailbox", "INBOX"))
            )
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
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})


@mail.route("/get_email", methods=["GET", "POST"])
@imap_authentication()
def imap_get_email(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    try:
        email_id = args.get("id", None)
        if email_id:
            imap_client.select(adjust_mailbox(args.get("mailbox", "INBOX")))
            stuats, data = imap_client.get_emails(email_id)

            output = None
            if (len(data) > 0):
                output = process_email_for_display(data[0])

            response = {"status": "OK", "data": output}
        else:
            response = {"status": "ERROR", 
                       "data": {"msg": "Unspecified e-mail's id."}}

        return jsonify(response)
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})


@mail.route("/move_emails", methods=["GET", "POST"])
@imap_authentication()
def imap_move_emails(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "ids" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined emails' ids."}})

    source_mailbox = args.get("source_mailbox", imap_client.mailbox)
    if not source_mailbox:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined source mailbox."}})

    dest_mailbox = args.get("dest_mailbox", None)
    if not dest_mailbox:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined destination mailbox."}})        

    try:
        imap_client.select(adjust_mailbox(source_mailbox))
        status, data = imap_client.move_emails(
                            args["ids"], adjust_mailbox(dest_mailbox)
                       )
        if status == "OK":
            return jsonify({"status": "OK", "data": data})
        else:
           return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})


# @mail.route("/remove_flags", defaults={"command": "remove"}, methods=["GET", "POST"])
# @mail.route("/set_flags", defaults={"command": "set"}, methods=["GET", "POST"])
# @mail.route("/add_flags", defaults={"command": "add"}, methods=["GET", "POST"])
@mail.route("/store/<string:command>", methods=["GET", "POST"])
@imap_authentication()
def imap_store(imap_client, command):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "ids" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined emails' ids."}})
    if "flags" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined flags."}})
    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox."}})

    methods = dict(ADD=imap_client.add_flags,REMOVE=imap_client.remove_flags,
                   SET=imap_client.set_flags)
    flags_method = methods.get(command.upper(), None)

    if not flags_method:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Unsupported command."}})

    try:
        imap_client.select(adjust_mailbox(args["mailbox"]))
        status, data = flags_method(args["ids"], args["flags"])
        if status != "OK":
            return jsonify({"status": "ERROR", "data": {"msg": data}}) 
        else:
            return jsonify({"status": "OK", "data": data})
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})      


@mail.route("/rename", methods=["GET", "POST"])
@imap_authentication()
def imap_rename(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "oldmailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined original mailbox name."}})
    if "newmailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined new mailbox name."}})

    try:
        status, data = imap_client.rename(
                            adjust_mailbox(args["oldmailbox"]), 
                            adjust_mailbox(utf7_encode(args["newmailbox"]))
                       )
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})      

    data = data[0].decode("ascii")    

    if status != "OK":
        return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    else:
        return jsonify({"status": "OK", "data": data})   


@mail.route("/create", methods=["GET", "POST"])
@imap_authentication()
def imap_create(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox name."}})

    try:
        status, data = imap_client.create(
                            adjust_mailbox(utf7_encode(args["mailbox"]))
                       )
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})  

    data = data[0].decode("ascii")    

    if status != "OK":
        return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    else:
        return jsonify({"status": "OK", "data": data})   


@mail.route("/delete", methods=["GET", "POST"])
@imap_authentication()
def imap_delete(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox name."}})

    try:
        status, data = imap_client.delete(adjust_mailbox(args["mailbox"]))
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})      

    data = data[0].decode("ascii")    

    if status != "OK":
        return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    else:
        return jsonify({"status": "OK", "data": data})   


@mail.route("/search", methods=["GET", "POST"])
@imap_authentication()
def imap_search(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox name."}})

    if "criteria" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined search criteria."}})

    criteria = json.loads(args["criteria"])
    try:
        imap_client.select(adjust_mailbox(args["mailbox"]))
        status, data = imap_client.csearch(criteria)
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})        

    if status != "OK":
        return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    else:
        return jsonify({"status": "OK", "data": data})


@mail.route("/len_mailbox", methods=["GET", "POST"])
@imap_authentication()
def imap_len_mailbox(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox name."}})

    try:
        status, data = imap_client.len_mailbox(adjust_mailbox(args["mailbox"]))
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})        

    if status != "OK":
        return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    else:
        return jsonify({"status": "OK", "data": data})


@mail.route("/list_mailbox", methods=["GET", "POST"])
@imap_authentication()
def imap_list_mailbox(imap_client):
    if request.method == "POST":
        args = request.form
    elif request.method == "GET":
        args = request.args

    if "mailbox" not in args:
        return jsonify({"status": "ERROR", 
                        "data": {"msg": "Undefined mailbox name."}})

    try:
        status, data = imap_client.list_mailbox(adjust_mailbox(args["mailbox"]))
    except ImapClientError as e:
        return jsonify({"status": "ERROR", "data": {"msg": str(e)}})     

    if status != "OK":
        return jsonify({"status": "ERROR", "data": {"msg": data}}) 
    else:
        return jsonify({"status": "OK", "data": data})


@mail.route("/integration", methods=["GET", "POST"])
@imap_authentication()
def integration(imap_client):
    return render_template("integration.html")    