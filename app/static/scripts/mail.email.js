$("#email-modal").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#email-subject").html("");
    $modal.find("#email-base").empty();
    $modal.find("#email-subject").html("Loading email ....");
    $modal.find("#email-header").hide();
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

$(document).on("click", "#email-header-more", function() {
    $("#email-header > tbody").children().not(":first-child").toggle();
    if ($(this).html() == "More") {
        $(this).html("Less");
    } else {
        $(this).html("More");
    }
    return false;
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
        $modal.find("#email-header").show();
        $modal.find("#email-header-from").html(
            email.header["From"].replace("<", "&lt").replace(">", "&gt")  +
            " (<a id='email-header-more' href='#'>More</a>)");
        $modal.find("#email-header-subject").html(
            email.header["Subject"].replace("<", "&lt").replace(">", "&gt"));
        $modal.find("#email-header-date").html(
            moment(email.header["Date"]).format("YYYY-MM-DD HH:mm"));
        $modal.find("#email-header-to").html(
            email.header["To"].replace("<", "&lt").replace(">", "&gt"));
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
        
        $emailPart = $("<li class='email-part email-plain'><iframe srcdoc='" +
            email.content.replace(/"/g, "&quot;").replace(/'/g, "&#039;") + 
            "'></iframe></li>");

        $emailPart = $("<li class='email-part email-plain'></li>");
        $emailPart.html(email.content);

    }
    if ($emailPart !== undefined) {
        $base.append($emailPart);
    }
}