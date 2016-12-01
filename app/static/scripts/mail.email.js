$("#email-modal").on("show.bs.modal", function(event) {
    var modal = $(this);

});

$("#email-modal").on("shown.bs.modal", function (event) {
    var $modal = $(this);

    var emailId = $modal.data("email-id");
    getEMails({
        ids: emailId.toString(),
        callback: updateEmailModal
    })
});


function updateEmailModal(response) {
    alert(response.status);
}