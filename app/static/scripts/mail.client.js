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

function updateMailboxesList(response) {
    if (response.status == "OK") {
        var mailboxes = response.data;
        
        var $list = $("#mailbox-list");
        for(var i = 0; i < mailboxes.length; i++) {
            var $mailbox = $("<li>" + mailboxes[i] + "</li>");
            $list.append($mailbox);
        }
    } else {
        alert("ERROR");
    }
}

function updateEMailsList(response) {
    if (response.status == "OK") {
        var emails = response.data;

        var $list = $("#emails-list");
        for (var i = 0; i < emails.length; i++) {
            var $email = $("<tr data-email-id='" + emails[i].id + "' " +
                           "class='email-header'></tr>");
            $email.append("<td>" + emails[i].From + "</td>");
            $email.append("<td>" + emails[i].Subject.substr(0, 100) + 
                          (emails[i].Subject.length > 100 ? " (...)" : "") +
                          "</td>");
            $email.append("<td>" + emails[i].Date + "</td>");
            $list.append($email);
        }
    } else {    
        alert("ERROR");
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
        from: options.from,
        to: options.to
    })
        .done(function(response) {
            if (options.callback !== undefined) {
                options.callback(response);
            }
        })
        .fail(function(response) {
             options.callback({
                    status: "ERROR",
                    data: response
                });
        });
}

function getEMails(options) {
    if (options === undefined) options = {};
    if (options.ids !== undefined) {
        $.post(settings.ajax_get_emails, {
            test: "Kuba",
            ids: options.ids
        })
            .done(function(response) {
                if (options.callback !== undefined) {
                    options.callback(response);
                }
            })
            .fail(function(response) {
                 options.callback({
                        status: "ERROR",
                        data: response
                    });
            });
    } else {
        throw "Undefined emails' ids.";
    }
}