/*******************************************************************************
    DEFAULTS
*******************************************************************************/

var settings = {
    default_mailbox: "INBOX",
    emails_per_page: 50,
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
        // this.mailbox = options.mailbox;
        // this.page = 1;
        this.emailsPerPage = options.emailsPerPage;
        this.requestInProgress = false;
        this.selectMailbox(options.mailbox);
    },
    selectMailbox: function(mailbox) {
        if (mailbox === undefined) mailbox = settings.default_mailbox;
        this.mailbox = mailbox;
        this.page = 1;
        this.total_emails = undefined;
        this.sendEMailsHeadersRequest();
        toggleActiveMailbox(mailbox);
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
        if (!this.requestInProgress) { // only one request at once
            var self = this; // required for callback
            this.requestInProgress = true;
            setInfo("Loading e-mails ...");
            getEMailsHeaders({
                from: this.calcFrom(this.page),
                to: this.calcTo(this.page),
                mailbox: this.mailbox,
                callback: function(response) {
                    setInfo("");
                    self.headersCallback(response, self);
                }
            });      
        }  
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
            alert("ERROR: " + JSON.stringify(response.data));
        }
    }
};

function setInfo(text) {
    $("#client-info").html(text);
}

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
            var $mailbox = $("<li data-name='" + 
                             mailboxes[i].utf7 + "'>" + 
                             mailboxes[i].utf16 + "</li>");
            $list.append($mailbox);
        }
    } else {
        alert("ERROR: " + JSON.stringify(response.data));
    }
}

function toggleActiveMailbox(mailbox) {
    if (mailbox === undefined) mailbox = EMailsListController.mailbox;
    if (mailbox) {
        var $list = $("#mailbox-list");
        $list.children(".active").removeClass("active");
        $list.children("[data-name='" + mailbox + "']").addClass("active");
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
            if (emails[i].Flags !== undefined) {
                var flags = emails[i].Flags.map(function(x) { return x.toUpperCase()});
                if (flags.indexOf("\\SEEN") < 0) {
                    $email.addClass("unseen");
                }
            }
            $email.append("<td class='email-controls'></td>");
            var $controls = $email.find(".email-controls");
            $controls.append("<span class='email-drag'>&#10697;</span>");
            $controls.append("<input class='email-check' type='checkbox'/>");
            $controls.append("<span class='email-star'>&#9733;</span>");

            $email.append("<td class='email-from email-open'>" + emails[i].From + "</td>");
            $email.append("<td class='email-subject email-open'>" + 
                          emails[i].Subject.substr(0, 100) + 
                          (emails[i].Subject.length > 100 ? " (...)" : "") +
                          "</td>");
            $email.append("<td class='email-date email-open'>" + 
                          moment(emails[i].Date).format("YYYY-MM-DD") + "</td>");
            $list.append($email);
        }
        toggleActiveMailbox();


        //http://stackoverflow.com/questions/3591264/can-table-rows-be-made-draggable
        $("#emails-list span.email-drag").draggable({
            helper: function() {
                // return $(this).parent().parent();
                return $("<div class='email-dragged'>E-Mail<div>");
            },
            start: function(event, ui) {
                // c.tr = this;
                // c.helper = ui.helper;
            }
        });


    } else {    
        alert("ERROR: " + JSON.stringify(response.data));
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