$("#email-modal").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#email-subject").html("");
    $modal.find("#email-base").empty();
    $modal.find("#email-subject").html("Loading email ....");
});

$("#email-modal").on("shown.bs.modal", function (event) {
    var $modal = $(this);
    var emailId = $modal.data("email-id");
    var mailbox = $modal.data("mailbox");
    getEMail({
        id: emailId.toString(),
        mailbox: mailbox,
        callback: updateEmailModal
    })
});

function updateEmailModal(response) {
    if (response.status == "OK") {
        var email = response.data;
        var $modal = $("#email-modal");
        if (email.header["Subject"] != "") {
            $modal.find("#email-subject").html(email.header["Subject"]);
        } else {
            $modal.find("#email-subject").html("&lt;No SUBJECT&gt;");
        }
        var $emailBase = $modal.find("#email-base");
        createEmailTree(email, $emailBase);
    } else {
        alert(JSON.stringify(response.data));
    }
}

function createEmailTree(email, $base) {
    var $emailPart = undefined;
    if (email.type == "node") {
        $emailPart = $("<li class='email-part email-node'></li>");
        var $emailNode = $("<ul class='email-part email-node'></ul>");
        for (var i = 0; i < email.content.length; i++) {
            createEmailTree(email.content[i], $emailNode);
        }
        $emailPart.append($emailNode);
    } else if (email.type == "plain") {

        if (navigator.userAgent.indexOf("MSIE") < 0) { // IE - IFRAME ERROR
            $emailPart = $("<li class='email-part email-plain'><iframe srcdoc='" +
                email.content.replace(/"/g, "&quot;").replace(/'/g, "&#039;") + 
                "'></iframe></li>");
        } else { // IE VERSION
            $emailPart = $("<li class='email-part email-plain'>" +
                email.content.replace(/"/g, "&quot;").replace(/'/g, "&#039;") + 
                "</li>");
        }
    }
    if ($emailPart !== undefined) {
        $base.append($emailPart);
    }
}