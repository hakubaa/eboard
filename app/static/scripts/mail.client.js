/******************************************************************************
    DEFAULTS
*******************************************************************************/

var settings = {
    default_mailbox: "INBOX",
    emails_per_page: 3,
    enable_uid: true,
    enable_caching: true
};

/*******************************************************************************
    Init 
*******************************************************************************/

/**
 * The manager of emails.
 * @type {EMailsIterator}
 */
var emanager;

function initClient() {
    emanager = new EMailsManager({
            emailsPerPage: settings.emails_per_page,
            uid: settings.enable_uid,
            caching: settings.enable_caching
    });
    emanager.on("onLoad", function() {
        setInfo("Loading e-mails ...");    
    });
    emanager.on("onLoaded", function(response) {
        if (response.status == "OK") {
            updateEMailsList(response);
            toggleActiveMailbox(emanager.getCurrentMailbox());
            updatePageInfo({
                from: 0,
                to: 0,
                total_emails: emanager.getEMailsCount()
            });
        } else {
            alert("ERROR: " + JSON.stringify(response.data));
        }
        setInfo("");
    });
    emanager.on("onUpdate", function() {
        setInfo("Updating source ...");
    });
    emanager.on("onUpdated", function(response) {
        if (response.status === "OK") {
            emanager.loadEMails(page=1);
        } else {
            alert("ERROR: " + JSON.stringify(response.data));
        }
    });
    emanager.setSource(new SelectSource({
            mailbox: settings.default_mailbox,
            uid: settings.enable_uid
        }));
    emanager.updateSource();  
    getMailboxes({callback: updateMailboxesList});

    $(document).mouseup(function (e) {
        var $searchMenu = $("#extended-emails-search");
        if (!$searchMenu.is(e.target) && $searchMenu.has(e.target).length === 0) {
            $searchMenu.hide();
        }
    });


    $(document).on("click", ".email-open", function() {
        $(this).parent().removeClass("unseen");
        $("#email-modal").data("email-id", $(this).parent().data("email-id"));
        $("#email-modal").data("mailbox", emanager.getCurrentMailbox());
        $("#email-modal").modal("show");
    });
    $(document).on("click", "#mailbox-list li", function() {
        emanager.setSource(new SelectSource({
                mailbox: $(this).data("name"),
                uid: settings.enable_uid
            }));
        emanager.updateSource();  
    });
    $("#prev-emails-btn").click(function() {
        emanager.prevPage();
    });
    $("#next-emails-btn").click(function() {
        emanager.nextPage();
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
        var mailbox = emanager.getCurrentMailbox();

        var $self = $(this);;
        setInfo("Updating e-mail's flags ...");
        updateFlags({
            ids: id, mailbox: mailbox, command: command,
            uid: settings.enable_uid,
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
        emanager.updateSource();
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
                        emanager.getCurrentMailbox() + "']").html();
        if (confirm("Are you sure you want to delete '" + mailbox + "' mailbox?")) {
            setInfo("Deleting mailbox ...");
            deleteMailbox({
                mailbox: emanager.getCurrentMailbox(),
                callback: function(response) {
                    if (response.status == "OK") {
                        getMailboxes({callback: updateMailboxesList});
                        emanager.setSource(new SelectSource({
                                mailbox: settings.default_mailbox,
                                uid: settings.enable_uid
                            }));
                        emanager.updateSource();  
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
                mailbox: emanager.getCurrentMailbox(), 
                uid: settings.enable_uid,
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
                mailbox: emanager.getCurrentMailbox(), 
                uid: settings.enable_uid,
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

    // $.datetimepicker.setLocale('en');
    // $('#email-search-date-from').datetimepicker({
    //     timepicker:false,
    //     format:'Y-m-d',
    //     theme: "dark"
    // });
    // $('#email-search-date-to').datetimepicker({
    //     timepicker:false,
    //     format:'Y-m-d',
    //     theme: "dark"
    // });

    $("#email-search-btn").click(function() {
        var text_val = $("#email-search-text").val();
        if (text_val !== "") {
            var source = new SearchSource({
                mailbox: $("#email-search-mailbox option:selected").data("name"),
                criteria: [
                    {key: "TEXT", value: text_val, decode: true}
                ],
                uid: settings.enable_uid
            });
            setInfo("Searching e-mails ...");  
            source.update(function(response) {
                setInfo("");
                if (response.status === "OK") {
                    var data = response.data;
                    if (data.length > 0) {
                        emanager.setSource(source);
                        emanager.loadEMails(page=1);
                    } else {
                        alert("No emails found.");
                    }
                } else {
                    alert("ERROR: " + JSON.stringify(response.data));  
                }
            });
        } 
    });
    
    $("#email-ext-search-btn").click(function() {
        var inputs = [
            { key: "FROM", dom: "#email-search-from", decode: true },
            { key: "TO", dom: "#email-search-to", decode: true },
            { key: "SUBJECT", dom: "#email-search-subject", decode: true },
            { key: "BODY", dom: "#email-search-body", decode: true }
        ];

        var criteria = inputs.map(function(item) {
            return ({
                key: item.key,
                value: $(item.dom).val(),
                decode: item.decode
            });     
        }).filter(function(item) {
            return (item.value !== "")
        });

        var date_from = $("#email-search-date-from").val();
        if (date_from !== "") {
            var date_from_m = moment(date_from, "YYYY-MM-DD");
            if (date_from_m.isValid()) {
                criteria.push({
                    key: "SENTSINCE",
                    value: date_from_m.format("D-MMM-YYYY"),
                    decode: false
                });
            } else {
                alert("Invalid format of 'from' date.");
            }
        }
        var date_to = $("#email-search-date-to").val();
        if (date_to !== "") {
            var date_to_m = moment(date_to, "YYYY-MM-DD");
            if (date_to_m.isValid()) {
                criteria.push({
                    key: "SENTBEFORE",
                    value: date_to_m.add(1, "day").format("D-MMM-YYYY"),
                    decode: false
                });
            } else {
                alert("Invalid format of 'to' date");
            }
        }

        var mailbox = $("#email-search-mailbox option:selected").data("name");

        if (criteria.length > 0) {
            var source = new SearchSource({
                mailbox: mailbox,
                criteria: criteria,
                uid: settings.enable_uid
            });
            setInfo("Searching e-mails ...");  
            source.update(function(response) {
                setInfo("");
                if (response.status === "OK") {
                    var data = response.data;
                    if (data.length > 0) {
                        emanager.setSource(source);
                        emanager.loadEMails(page=1);
                    } else {
                        alert("No emails found.");
                    }
                } else {
                    alert("ERROR: " + JSON.stringify(response.data));  
                }
            });
        } else {
            alert("You have not specified any criteria.");
        }
    });
}

/*******************************************************************************
    Functions
*******************************************************************************/

function initSearchSource(mailbox, criteria) {
    var source = new SearchSource();
    setInfo("Searching e-mails ...");
    source.load({
        mailbox: mailbox,
        criteria: criteria,
        uid: settings.enable_uid,
        callback: function(response) {
            setInfo("");
            if (response.status === "OK") {
                emanager.loadEMails(page=1);
            } else {
                alert("ERROR: " + JSON.stringify(response.data));
            }
        }
    });   
}

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

        var $searchList = $("#email-search-mailbox");
        $searchList.empty();

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

            $searchList.append("<option data-name='" + mailboxes[i].utf7 + "' " +
                               (flags.indexOf("\\ALL") >= 0 ? "selected" : "") + 
                               ">" + mailboxes[i].utf16 + "</option>");
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
        uid: settings.enable_uid,
        source_mailbox: emanager.getCurrentMailbox(),
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
    if (mailbox === undefined) mailbox = emanager.getCurrentMailbox();
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

/*****************************************************************************/