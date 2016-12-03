/*******************************************************************************
    DEFAULTS
*******************************************************************************/

var settings = {
    default_mailbox: "INBOX",
    emails_per_page: 25,
    ajax_list: "/mail/list",
    ajax_get_headers: "/mail/get_headers",
    ajax_get_emails: "/mail/get_emails"
};

/*******************************************************************************
    UI controllers
*******************************************************************************/

var EMailsListController = {
    init: function(options) {
        if (options === undefined) options = {};
        if (options.emailsPerPage === undefined) {
            options.emailsPerPage = settings.emails_per_page;
        }
        if (options.mailbox === undefined) {
            options.mailbox = settings.default_mailbox;
        }
        this.mailbox = options.mailbox;
        this.page = 1;
        this.emailsPerPage = options.emailsPerPage;
        this.total_emails = undefined;
        this.requestInProgress = false;
        this.sendEMailsHeadersRequest();
    },
    getNextEMails: function() {
        var nextFrom = this.calcFrom(this.page + 1);
        var nextTo = this.calcTo(this.page + 1);
        if (this.total_emails !== undefined) {
            nextTo = Math.min(nextTo, this.total_emails);
        }
        if (nextTo > nextFrom) {
            this.page += 1;
            this.sendEMailsHeadersRequest();
        }
    },
    getCurrentEMails: function() {
        this.sendEMailsHeadersRequest();    
    },
    getPrevEMails: function() {
        if (this.page > 1) {
            this.page -= 1;
            this.sendEMailsHeadersRequest();
        }
    },
    sendEMailsHeadersRequest: function() {
        var self = this;
        this.requestInProgress = true;
        getEMailsHeaders({
            from: this.calcFrom(this.page),
            to: this.calcTo(this.page),
            mailbox: this.mailbox,
            callback: function(response) {
                self.headersCallback(response, self);
            }
        });        
    },
    calcFrom: function(page) {
        if (page === undefined || page === null || page == 0) {
            return 1;
        }
        var emailsFrom = 1 + (page - 1)*this.emailsPerPage;
        if (this.total_emails !== undefined)
            emailsFrom = Math.min(emailsFrom, this.total_emails)
        return emailsFrom;
    },
    calcTo: function(page) {
        if (page === undefined || page === null || page == 0) {
            return Math.min(this.emailsPerPage, this.total_emails);
        } 
        var emailsTo = page * this.emailsPerPage;
        if (this.total_emails !== undefined)
            emailsTo = Math.min(emailsTo, this.total_emails)     
        return emailsTo;
    },
    headersCallback: function(response, self) {
        if (self === undefined) self = this;

        self.requestInProgress = false;
        if (response.status == "OK") {
            self.total_emails = response.total_emails;
            updateEMailsList(response);
            updatePageInfo({
                from: self.calcFrom(self.page),
                to: self.calcTo(self.page),
                total_emails: self.total_emails
            });
        } else {
            alert("ERROR: " + JSON.parse(response.data));
        }
    }
};

function updatePageInfo(options) {
    var $page = $("#page-emails");
    $page.html(options.from + " - " + options.to + " of " + 
               options.total_emails);
}

function updateMailboxesList(response) {
    if (response.status == "OK") {
        var mailboxes = response.data;
        
        var $list = $("#mailbox-list");
        for(var i = 0; i < mailboxes.length; i++) {
            var $mailbox = $("<li>" + mailboxes[i] + "</li>");
            $list.append($mailbox);
        }
    } else {
        alert("ERROR: " + JSON.parse(response.data));
    }
}

function updateEMailsList(response) {
    if (response.status == "OK") {
        var emails = response.data;
        var $list = $("#emails-list > tbody");
        $list.empty();
        for (var i = 0; i < emails.length; i++) {
            var $email = $("<tr data-email-id='" + emails[i].id + "' " +
                           "class='email-header'></tr>");
            $email.append("<td class='email-from'>" + emails[i].From + "</td>");
            $email.append("<td class='email-subject'>" + 
                          emails[i].Subject.substr(0, 100) + 
                          (emails[i].Subject.length > 100 ? " (...)" : "") +
                          "</td>");
            $email.append("<td class='email-date'>" + 
                          moment(emails[i].Date).format("YYYY-MM-DD") + "</td>");
            $list.append($email);
        }
    } else {    
        alert("ERROR: " + JSON.parse(response.data));
    }
}

/*******************************************************************************
    XMLHttpRequest handlers
*******************************************************************************/

function getMailboxes(options) {
    if (options === undefined) options = {};

    $.post(settings.ajax_list)
        .done(function(response) {
            if (options.callback !== undefined) {
                options.callback(response);
            }
        })
        .fail(function(response) {
            if (options.callback !== undefined) {
                options.callback({
                    status: "ERROR",
                    data: response
                });
            }
        });
}

function getEMailsHeaders(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) options.mailbox = settings.default_mailbox;
    if (options.from === undefined) options.from = 0;
    if (options.to === undefined) options.to = options.from + 
                                               settings.emails_per_page;

    $.post(settings.ajax_get_headers, {
        mailbox: options.mailbox,
        ids_from: options.from,
        ids_to: options.to
    })
        .done(function(response) {
            if (options.callback !== undefined) {
                options.callback(response);
            }
        })
        .fail(function(response) {
            if (options.callback !== undefined) {
                options.callback({
                    status: "ERROR",
                    data: response
                });
            }
        });
}

function getEMails(options) {
    if (options === undefined) options = {};
    if (options.ids !== undefined) {
        $.post(settings.ajax_get_emails, {
            ids: options.ids
        })
            .done(function(response) {
                if (options.callback !== undefined) {
                    options.callback(response);
                }
            })
            .fail(function(response) {
                if (options.callback !== undefined) {
                    options.callback({
                        status: "ERROR",
                        data: response
                    });
                }
            });
    } else {
        throw "Undefined emails' ids.";
    }
}

/******************************************************************************/