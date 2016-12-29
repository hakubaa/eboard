/**
 * @dict
 */
var ajax_urls = {
    list: "/mail/list",
    get_headers: "/mail/get_headers",
    get_raw_emails: "/mail/get_raw_emails",
    get_email: "/mail/get_email",
    move_emails: "/mail/move_emails",
    flags_add: "/mail/add_flags",
    flags_remove: "/mail/remove_flags",
    flags_set: "/mail/set_flags",
    store: "/mail/store",
    create_mailbox: "/mail/create",
    rename_mailbox: "/mail/rename",
    delete_mailbox: "/mail/delete",
    search_emails: "/mail/search",
    len_mailbox: "/mail/len_mailbox",
    list_mailbox: "/mail/list_mailbox"
};

/**
 * Send XMLHttpRequest 
 * @param {string} url URL.
 * @param {Object} params Dictionary with parameters.
 * @param {function} callback Function called after response.
 */
 function sendRequest(url, params, callback) {
     $.post(url, params)
        .done(function(response) {
            if (callback !== undefined) {
                callback(response);
            }
        })
        .fail(function(response) {
            if (callback !== undefined) {
                callback({
                    status: "ERROR",
                    data: response
                });
            }
        });   
 }

/**
 * Send XMLHttpRequest for e-mails headers.
 * @param {Object} options 
 */
function getEMailsHeaders(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw "Undefined 'mailbox' argument.";   
    }
    if (options.from === undefined) options.from = 0;
    if (options.to === undefined && options.ids === undefined) {
        throw "Undefined 'to'/'ids' argument.";
    }
    if (options.uid === undefined) options.uid = false;

    var params;
    if (options.ids !== undefined) {
        params = {
            mailbox: options.mailbox,
            ids: options.ids,
            uid: options.uid
        };   
    } else {
        params = {
            mailbox: options.mailbox,
            ids_from: options.from,
            ids_to: options.to
        };          
    }

    sendRequest(ajax_urls.get_headers, params, options.callback);
}

/**
 * Send XMLHttpRequest for e-mails which meet specified criteria.
 * @param {Object} options 
 */
function searchEMails(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw "Undefined mailbox.";
    }
    if (options.criteria === undefined) {
        throw "Undefined criteria.";
    }
    if (options.uid === undefined) options.uid = false;

    sendRequest(ajax_urls.search_emails, {
            mailbox: options.mailbox,
            criteria: JSON.stringify(options.criteria),
            uid: options.uid
        }, 
        options.callback);
}

/**
 * Send XMLHttpRequest for number of emails in mailbox.
 * @param {Object} options 
 */
function getEMailsCount(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw "Undefined mailbox.";
    }

    sendRequest(ajax_urls.len_mailbox, {mailbox: options.mailbox}, 
                options.callback);
}

/**
 * Send XMLHttpRequest for list of emails in the mailbox
 * @param {Object} options
 */
function getEMailsList(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw "Undefined mailbox.";
    }
    sendRequest(ajax_urls.list_mailbox, 
                {mailbox: options.mailbox, uid: options.uid},
                options.callback);
}

/**
 * Send XMLHttpRequest for update flags of selected e-mails.
 * @param {Object} options
 */
function updateFlags(options) {
    if (options === undefined) options = {};
    if (options.command === undefined) {
        throw "Undefined command.";
    }
    if (options.flags === undefined) {
        throw "Undefined flags.";
    }
    if (options.ids === undefined) {
        throw "Undefined emails' ids.";
    }
    if (options.mailbox === undefined) {
        throw "Undefined mailbox.";
    }
    if (options.uid === undefined) options.uid = false;

    $.post(ajax_urls.store + "/" + options.command, {
        ids: options.ids,
        flags: options.flags,
        mailbox: options.mailbox,
        uid: options.uid
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

/**
 * Send XMLHttpRequest for moving selected e-mails between mailboxes.
 * @param {Object} options
 */
function moveEMails(options) {
    if (options === undefined) options = {};
    if (options.ids === undefined) {
        throw "Undefined emails' ids.";
    }
    if (options.dest_mailbox === undefined) {
        throw "Undefined destination mailbox.";
    }
    if (options.source_mailbox === undefined) {
        throw "Undefined source mailbox.";
    }
    if (options.uid === undefined) options.uid = false;

    $.post(ajax_urls.move_emails, {
        ids: options.ids,
        dest_mailbox: options.dest_mailbox,
        source_mailbox: options.source_mailbox,
        uid: options.uid
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

/**
 * Send XMLHttpRequest for list of mailboxes.
 * @param {Object} options
 */
function getMailboxes(options) {
    if (options === undefined) options = {};

    $.post(ajax_urls.list)
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

/**
 * Send XMLHttpRequest for raw e-mails.
 * @param {Object} options
 */
function getRawEMails(options) {
    if (options === undefined) options = {};
    if (options.uid === undefined) options.uid = false;

    if (options.ids !== undefined) {
        $.post(ajax_urls.get_raw_emails, {
            ids: options.ids,
            uid: options.uid
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

/**
 * Send XMLHttpRequest for formated e-mail.
 * @param {Object} options
 */
function getEMail(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) options.mailbox = settings.default_mailbox;
    if (options.uid === undefined) options.uid = false;

    if (options.id !== undefined) {
        $.post(ajax_urls.get_email, {
            id: options.id,
            mailbox: options.mailbox,
            uid: options.uid
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
        throw "Undefined email's id.";
    }
}

/**
 * Send XMLHttpRequest to create new mailbox.
 * @param {Object} options
 */
function createMailbox(options) {
    if (options === undefined) options = {};
    if (options.mailbox !== undefined) {
        $.post(ajax_urls.create_mailbox, {
            mailbox: options.mailbox
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
        throw "Undefined mailbox name.";
    }
}

/**
 * Send XMLHttpRequest to delete the mailbox.
 * @param {Object} options
 */
function deleteMailbox(options) {
    if (options === undefined) options = {};
    if (options.mailbox !== undefined) {
        $.post(ajax_urls.delete_mailbox, {
            mailbox: options.mailbox
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
        throw "Undefined mailbox name.";
    }
}

/**
 * Send XMLHttpRequest to rename the mailbox.
 * @param {Object} options
 */
function renameMailbox(options) {
    if (options === undefined) options = {};

    if (options.newmailbox === undefined) {
        throw "Undefined new mailbox name.";
    }
    if (options.oldmailbox === undefined) {
        throw "Undefined original mailbox name.";
    }

    $.post(ajax_urls.rename_mailbox, {
        oldmailbox: options.oldmailbox,
        newmailbox: options.newmailbox
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