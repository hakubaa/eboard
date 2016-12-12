$("#email-modal").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find(".email-element").html("");
    $modal.find("#email-subject").html("Loading email ....");
});

$("#email-modal").on("shown.bs.modal", function (event) {
    var $modal = $(this);
    var emailId = $modal.data("email-id");
    getEMail({
        id: emailId.toString(),
        callback: updateEmailModal
    })
});

function updateEmailModal(response) {
    if (response.status == "OK") {
        var email = response.data;
        var $modal = $("#email-modal");
        $modal.find("#email-subject").html(email.header["Subject"]);
        $modal.find("#email-body").html(email.body);
    } else {
        alert(JSON.stringify(response.data));
    }
}