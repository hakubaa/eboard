$("#mailbox-modal").on("show.bs.modal", function(event) {
    $("#mailboxName").val("");
});

$("#create-mailbox-btn").click(function() {
    var mailbox = $("#mailboxName").val();
    if (mailbox === "") {
        alert("Empty mailbox name. Please enter mailbox name in order " +
              "to create new mailbox.");
    } else {
        createMailbox({
            mailbox: mailbox,
            callback: function(response) {
                if (response.status == "OK") {
                    getMailboxes({callback: updateMailboxesList});
                    alert("Mailbox '" + mailbox + "' has been successfully created.");
                    $("#mailbox-modal").modal("hide");
                } else {
                    alert("Unable to create mailbox with given name: " +
                          response.data.msg !== undefined ? response.data.msg : response.data);
                }
            }
        })
    }
});