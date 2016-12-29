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
    len_mailbox: "/mail/len_mailbox"
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

    var params;
    if (options.ids !== undefined) {
        params = {
            mailbox: options.mailbox,
            ids: options.ids
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
    sendRequest(ajax_urls.search_emails, {
            mailbox: options.mailbox,
            criteria: JSON.stringify(options.criteria)
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
    $.post(ajax_urls.store + "/" + options.command, {
        ids: options.ids,
        flags: options.flags,
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
}

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
    $.post(ajax_urls.move_emails, {
        ids: options.ids,
        dest_mailbox: options.dest_mailbox,
        source_mailbox: options.source_mailbox
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

function getRawEMails(options) {
    if (options === undefined) options = {};
    if (options.ids !== undefined) {
        $.post(ajax_urls.get_raw_emails, {
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

function getEMail(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) options.mailbox = settings.default_mailbox;
    if (options.id !== undefined) {
        $.post(ajax_urls.get_email, {
            id: options.id,
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
        throw "Undefined email's id.";
    }
}

// NO TESTS
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

// NO TESTS
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

// NO TESTS
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