/******************************************************************************
    DEFAULTS
*******************************************************************************/

var settings = {
    default_mailbox: "INBOX",
    emails_per_page: 50,
    ajax_list: "/mail/list",
    ajax_get_headers: "/mail/get_headers",
    ajax_get_raw_emails: "/mail/get_raw_emails",
    ajax_get_email: "/mail/get_email",
    ajax_move_emails: "/mail/move_emails",
    ajax_flags_add: "/mail/add_flags",
    ajax_flags_remove: "/mail/remove_flags",
    ajax_flags_set: "/mail/set_flags",
    ajax_store: "/mail/store",
    ajax_create_mailbox: "/mail/create",
    ajax_rename_mailbox: "/mail/rename",
    ajax_delete_mailbox: "/mail/delete"
};

/*******************************************************************************
    Init 
*******************************************************************************/

function initClient() {
    // getMailboxes({callback: updateMailboxesList});
    // EMailsListController.init({mailbox: settings.default_mailbox});

    $(document).on("click", ".email-open", function() {
        $(this).parent().removeClass("unseen");
        $("#email-modal").data("email-id", $(this).parent().data("email-id"));
        $("#email-modal").data("mailbox", EMailsListController.mailbox);
        $("#email-modal").modal("show");
    });
    $(document).on("click", "#mailbox-list li", function() {
        EMailsListController.selectMailbox($(this).data("name"));
    });
    $("#prev-emails-btn").click(function() {
        EMailsListController.getPrevEMails();
    });
    $("#next-emails-btn").click(function() {
        EMailsListController.getNextEMails();
    });    
    $(".select-emails").click(function() {
        var mode = $(this).data("select-type");
        selectEMails(mode);
    });   

    // Determine whether to swtich ALL/NONE when checkboxes change. 
    $(document).on("click", ".email-check", function() {
        updateSelectBtn();
    });

    $(document).on("click", ".email-star", function() {
        var command = "add";
        if ($(this).hasClass("flagged")) {
            command = "remove";
        }
        var id = $(this).parent().parent().data("email-id");
        var mailbox = EMailsListController.mailbox;

        var $self = $(this);;
        setInfo("Updating e-mail's flags ...");
        updateFlags({
            ids: id, mailbox: mailbox, command: command,
            flags: "\\Flagged",
            callback: function(response) {
                if (response.status === "OK") {
                    $self.toggleClass("flagged");
                    $self.parent().parent().toggleClass("flagged");
                } else {
                    alert(JSON.stringify(response.data));
                }
                setInfo("");
            }
        });
    });

    $("#extended-search-btn").click(function() {
        $("#extended-emails-search").toggle();
    });

    $("#archive-btn").click(function() {
        var mailbox = $("#mailbox-list").children().filter(function() {
            return ($(this).data("flags").indexOf("\\ALL") >= 0);
        }).first();
        if (mailbox.length > 0) {
            var $emails = $(".email-record")
                .filter(function() {
                    return ($(this).find(".email-check").is(":checked"));
                });
            if ($emails.length > 0) {
                moveSelectedEMails($(mailbox).data("name"), $emails);
            } else {
                alert("No emails selected.");
            }
        } else {
            alert("Archive mailbox not recognized. Please make sure your " +
                  "service provider implements special-use mailboxes.");
        }
    });

    $("#spam-btn").click(function() {
        var mailbox = $("#mailbox-list").children().filter(function() {
            return ($(this).data("flags").indexOf("\\JUNK") >= 0);
        }).first();
        if (mailbox.length > 0) {
            var $emails = $(".email-record")
                .filter(function() {
                    return ($(this).find(".email-check").is(":checked"));
                });
            if ($emails.length > 0) {
                moveSelectedEMails($(mailbox).data("name"), $emails);
            } else {
                alert("No emails selected.");
            }
        } else {
            alert("Spam mailbox not recognized. Please make sure your " +
                  "service provider implements special-use mailboxes.");
        }
    });

    $("#remove-btn").click(function() {
        var mailbox = $("#mailbox-list").children().filter(function() {
            return ($(this).data("flags").indexOf("\\TRASH") >= 0);
        }).first();
        if (mailbox.length > 0) {
            var $emails = $(".email-record")
                .filter(function() {
                    return ($(this).find(".email-check").is(":checked"));
                });
            if ($emails.length > 0) {
                moveSelectedEMails($(mailbox).data("name"), $emails);
            } else {
                alert("No emails selected.");
            }
        } else {
            alert("Trash mailbox not recognized. Please make sure your " +
                  "service provider implements special-use mailboxes.");
        }
    });

    $("#refresh-btn").click(function() {
        EMailsListController.init({mailbox: EMailsListController.mailbox});
    });

    $(document).on("click", ".move-to-btn", function() {
        var mailbox = $(this).parent().data("name");
        var $emails = $(".email-record")
            .filter(function() {
                return ($(this).find(".email-check").is(":checked"));
            });
        moveSelectedEMails(mailbox, $emails);
    });

    $("#more-delete-mailbox").click(function() {
        var mailbox = $("#mailbox-list").find("[data-name='" + 
                        EMailsListController.mailbox + "']").html();
        if (confirm("Are you sure you want to delete '" + mailbox + "' mailbox?")) {
            setInfo("Deleting mailbox ...");
            deleteMailbox({
                mailbox: EMailsListController.mailbox,
                callback: function(response) {
                    if (response.status == "OK") {
                        getMailboxes({callback: updateMailboxesList});
                        EMailsListController.init({mailbox: settings.default_mailbox});
                        alert("Mailbox '" + mailbox + "' has been " +
                              "successfully deleted.");
                    } else {
                        alert("Unable to delete mailbox: " +
                              response.data.msg !== undefined ? response.data.msg : response.data);
                    }
                    setInfo("");
                }
            });
        }
        return false;
    });

    $("#more-unread").click(function() {
        var $emails = $(".email-record").not(".unseen")
            .filter(function() {
                return ($(this).find(".email-check").is(":checked"));
            });

        if ($emails.length > 0) {
            var emailsIds = $emails.map(function() {
                    return ($(this).data("email-id"));
                }).toArray();

            setInfo("Updating e-mail's flags ...");
            updateFlags({
                ids: emailsIds.join(), 
                mailbox: EMailsListController.mailbox, 
                command: "remove",
                flags: "\\Seen",
                callback: function(response) {
                    if (response.status === "OK") {
                        $emails.addClass("unseen");
                    } else {
                        alert(JSON.stringify(response.data));
                    }
                    setInfo("");
                }
            });

        }
        return false;
    });

    $("#more-read").click(function() {
        var $emails = $(".email-record.unseen")
            .filter(function() {
                return ($(this).find(".email-check").is(":checked"));
            });

        if ($emails.length > 0) {
            var emailsIds = $emails.map(function() {
                    return ($(this).data("email-id"));
                }).toArray();

            setInfo("Updating e-mail's flags ...");
            updateFlags({
                ids: emailsIds.join(), 
                mailbox: EMailsListController.mailbox, 
                command: "add",
                flags: "\\Seen",
                callback: function(response) {
                    if (response.status === "OK") {
                        $emails.removeClass("unseen");
                    } else {
                        alert(JSON.stringify(response.data));
                    }
                    setInfo("");
                }
            });

        }
        return false;
    });
}

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
            toggleActiveMailbox(self.mailbox);
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
        $list.empty();

        var $moveToList = $("#move-to-list-btn > ul");
        $moveToList.children().not(".const-item").remove();

        for(var i = 0; i < mailboxes.length; i++) {
            var flags = mailboxes[i].flags.join(" ").toUpperCase();
            if (flags.indexOf("\\NOSELECT") >= 0) {
                continue;
            }
            var $mailbox = $("<li data-name='" + mailboxes[i].utf7 + "' " +
                             "data-flags='" + flags + "'>" + 
                             mailboxes[i].utf16 + "</li>");
            $mailbox.droppable({
                classes: {
                    "ui-droppable-hover": "droppable-hover" 
                },
                drop: function(event, ui) {
                    var mailbox = $(this).data("name");
                    var $emails = $(".email-record")
                        .filter(function() {
                            return ($(this).find(".email-check").is(":checked") 
                                    || $(this).is(ui.draggable));
                        });
                    moveSelectedEMails(mailbox, $emails);
                }
            });
            $list.append($mailbox);

            var $li = $("<li data-name='" + mailboxes[i].utf7 + "' " +
                             "data-flags='" + flags + "'>" +
                             "<a class='move-to-btn' href='#'>" + 
                             mailboxes[i].utf16 + "</a></li>");
            $moveToList.prepend($li);
        }
        toggleActiveMailbox();
    } else {
        alert("ERROR: " + JSON.stringify(response.data));
    }
}

function moveSelectedEMails(mailbox, $emails) {
    var emailsIds = $emails.map(function() {
            return ($(this).data("email-id"));
        }).toArray();

    setInfo("Moving e-mails ...");
    moveEMails({
        ids: emailsIds.join(),
        source_mailbox: EMailsListController.mailbox,
        dest_mailbox: mailbox,
        callback: function(response) {
            setInfo("");
            if (response.status == "OK") {
                $emails.remove();
                updateSelectBtn();
            } else {
                alert(JSON.stringify(response.data));
            }
        }
    });
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
                           "class='email-record'></tr>");
            if (emails[i].Flags !== undefined) {
                var flags = emails[i].Flags.map(function(x) { return x.toUpperCase()});
                if (flags.indexOf("\\SEEN") < 0) {
                    $email.addClass("unseen");
                }

            }
            $email.append("<td class='email-controls email-small'></td>");
            var $controls = $email.find(".email-controls");
            $controls.append("<input class='email-check' type='checkbox'/>");

            var $star = $("<span class='email-star'>&#9733;</span>");
            if (flags.indexOf("\\FLAGGED") >= 0) {
                $star.addClass("flagged");
                $email.addClass("flagged");
            }
            $controls.append($star);

            var ctype = "undefined";
            if (emails[i]["Content-Type"] !== undefined) {
                ctype = emails[i]["Content-Type"].split(";")[0];
            }
            $email.append("<td class='email-from email-open'>" + emails[i].From + "</td>");
            $email.append("<td class='email-subject email-open'>" + 
                          emails[i].Subject.substr(0, 100) + 
                          (emails[i].Subject.length > 100 ? " (...)" : "") +
                          " #" + ctype + "" +
                          "</td>");
            $email.append("<td class='email-date email-open'>" + 
                          moment(emails[i].Date).format("YYYY-MM-DD") + "</td>");

            $email.append("<td class='email-small email-open'>From <strong>" + 
                          emails[i].From + "</strong> on <strong>" + 
                          moment(emails[i].Date).format("YYYY-MM-DD") + 
                          "</strong><br>" + 
                          emails[i].Subject.substr(0, 100) + 
                          (emails[i].Subject.length > 100 ? " (...)" : "") +
                          "</td>");

            $list.append($email);
        }

        //http://stackoverflow.com/questions/3591264/can-table-rows-be-made-draggable
        $("#emails-list .email-record").draggable({
            helper: function() {
                var $self = $(this)[0];
                var numOfEmails = $(".email-record").filter(function() {
                    return ($(this).find(".email-check").is(":checked") 
                            && $(this)[0] != $self);
                }).length + 1;
                return $("<div class='email-dragged-helper'>Dragging " + 
                    + numOfEmails + " emails.<div>");
            },
            start: function(event, ui) {
                $(this).addClass("email-dragged");
                $(".email-record").filter(function() {
                    return ($(this).find(".email-check").is(":checked"));
                }).addClass("email-dragged");
            },
            stop: function(event, ui) {
                $(this).removeClass("email-dragged");
                $(".email-record").filter(function() {
                    return ($(this).find(".email-check").is(":checked"));
                }).removeClass("email-dragged");
            },
            cursorAt: { left: 10, top: 10 }
        });

        // Reset select emails buttons
        updateSelectBtn();
    } else {    
        alert("ERROR: " + JSON.stringify(response.data));
    }
}

function updateSelectBtn() {
    var checks = $(".email-check").map(function() {
        return ($(this).is(":checked"));
    }).toArray();

    if (checks.every(function(item) { return (item === true); })) {
        $("#select-emails-btn").html("NONE");
        $("#select-emails-btn").data("select-type", "NONE"); 
    } else if (checks.every(function(item) { return (item === false); })) {
        $("#select-emails-btn").html("ALL");
        $("#select-emails-btn").data("select-type", "ALL");             
    }

    if (checks.some(function(item) { return (item === true); })) {
        $("#archive-btn").show();
        $("#spam-btn").show();
        $("#remove-btn").show();
        $("#move-to-list-btn").show();
        $(".more-emails").show();
    } else {
        $("#archive-btn").hide();
        $("#spam-btn").hide();
        $("#remove-btn").hide();
        $("#move-to-list-btn").hide();
        $(".more-emails").hide();
    }
}

function selectEMails(mode) {
    if (mode !== undefined) {
        if (mode === "ALL") {
            $(".email-record .email-check").prop("checked", true);
        } else if (mode === "NONE") {
            $(".email-record .email-check").prop("checked", false);
        } else if (mode === "READ") {
            $(".email-record").not("unseen").find(".email-check").prop("checked", true);
            $(".email-record.unseen").find(".email-check").prop("checked", false);
        } else if (mode === "UNREAD") {
            $(".email-record").not("unseen").find(".email-check").prop("checked", false);
            $(".email-record.unseen").find(".email-check").prop("checked", true);   
        } else if (mode === "STARRED") {
            $(".email-record").not("flagged").find(".email-check").prop("checked", false);
            $(".email-record.flagged").find(".email-check").prop("checked", true);   
        } else if (mode === "UNSTARRED") {
            $(".email-record").not("flagged").find(".email-check").prop("checked", true);
            $(".email-record.flagged").find(".email-check").prop("checked", false);   
        }
        updateSelectBtn();
    }
}

/*******************************************************************************
    XMLHttpRequest handlers
*******************************************************************************/

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
    $.post(settings.ajax_store + "/" + options.command, {
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
    $.post(settings.ajax_move_emails, {
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

function getRawEMails(options) {
    if (options === undefined) options = {};
    if (options.ids !== undefined) {
        $.post(settings.ajax_get_raw_emails, {
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
        $.post(settings.ajax_get_email, {
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
        $.post(settings.ajax_create_mailbox, {
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
        $.post(settings.ajax_delete_mailbox, {
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

    $.post(settings.ajax_rename_mailbox, {
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

/*****************************************************************************/