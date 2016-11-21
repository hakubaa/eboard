import json
import re

from flask import (
    render_template, redirect, url_for, request, flash, g,
    jsonify
)
from flask_login import current_user, login_required

from . import mail
from .forms import LoginForm
from .client import ImapClient


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
        except:
            flash("Unable to connect with service provider. Pleade verify " + 
                  "whether the imap address is correct.")

        if imap_client:
            try:
                imap_client.login(username, password)
            except:
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


@mail.route("/list_mailbox", methods=["GET", "POST"])
def imap_list_mailbox():
    imap_client = imap_clients.get(current_user.id, None)
    if imap_client:
        status, data = imap_client.list()
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
            "data": { "msg": "Not authorized access." } 
        }
    return jsonify(response)