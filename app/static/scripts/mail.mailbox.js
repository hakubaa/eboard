$("#mailbox-modal").on("show.bs.modal", function(event) {
    var action = $(event.relatedTarget).data("action");
    $(this).data("action", action);
    $("#mailboxName").val("");

    if (action === "create") {
        $(this).find(".modal-header").html("Create New Mailbox");
        $(this).find("#create-mailbox-btn").html("Create");
    } else if (action === "rename") {
        var mailbox = $("#mailbox-list").find("[data-name='" + 
                        EMailsListController.mailbox + "']").html();
        $(this).find(".modal-header").html("Rename Mailbox '" + mailbox + "'");
        $(this).find("#create-mailbox-btn").html("Rename");
    }
});

$("#create-mailbox-btn").click(function() {
    var mailbox = $("#mailboxName").val();
    var action = $("#mailbox-modal").data("action");

    if (mailbox === "") {
        alert("Empty mailbox name. Please enter mailbox name in order " +
              "to create new mailbox.");
    } else {

        if (action === "create") {

            createMailbox({
                mailbox: mailbox,
                callback: function(response) {
                    if (response.status == "OK") {
                        getMailboxes({callback: updateMailboxesList});
                        alert("The mailbox '" + mailbox + "' has been "+ 
                              "successfully created.");
                        $("#mailbox-modal").modal("hide");
                    } else {
                        alert("Unable to create the mailbox: " +
                              response.data.msg !== undefined ? response.data.msg : response.data);
                    }
                }
            });

        } else if (action == "rename") {

            renameMailbox({
                oldmailbox: EMailsListController.mailbox,
                newmailbox: mailbox,
                callback: function(response) {
                    if (response.status == "OK") {
                        getMailboxes({
                            callback: function(response) {
                                // Update name of active mailbox stored
                                // in EMailsListController. 
                                if (response.status == "OK") {
                                    var mboxes = response.data.filter(
                                        function(item) {
                                            return (item.utf16 == mailbox);
                                        }
                                    );
                                    if (mboxes.length > 0) {
                                        EMailsListController.mailbox = mboxes[0].utf7;
                                    }
                                }
                                updateMailboxesList(response);
                            }
                        });
                        alert("The mailbox '" + mailbox + "' has been successfully renamed.");
                        $("#mailbox-modal").modal("hide");
                    } else {
                        alert("Unable to rename the mailbox: " +
                              response.data.msg !== undefined ? response.data.msg : response.data);
                    }        
                }
            });  
                      
        }
    }
});