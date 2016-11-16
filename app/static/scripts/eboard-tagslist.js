var tagsPicker = {};

$("#new-tag-btn").click(function(event) {
    var tagName = $("#new-tag-name").val();
    if (tagName) {
        if (!/^[a-zA-Z0-9\s_]+$/.test(tagName)) {
            alert("Not allowed signs. Please use only letters, numbers and following signs: space, underscore.");
        } else {                             
            $.ajax({
                url: '/eboard/tasks/newtag',
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify({ tagname: tagName }),
                cache: false,
                dataType: "json",
                success: function(response) {
                    if (response.status == "success") {
                        for (var key in tagsPicker) {
                            if (tagsPicker.hasOwnProperty(key)) {
                                tagsPicker[key].addTag(response.data.id, response.data.name, 
                                    tagsPicker[key].isActive());
                            }
                        }
                    }
                    $('#new-tag-model').modal('hide');
                }
            }); 
        }
    } else {
        alert("Tag name's field is empty. Please enter valid tag name.");
    }  
});

$('#new-tag-model').on('hidden.bs.modal', function () {
    for (var key in tagsPicker) {
        if (tagsPicker.hasOwnProperty(key)) {
            tagsPicker[key].setActive(false);    
        }
    }
});

function createTagElement(value, name, onclick) {
    var div = document.createElement("div");

    var spanX = document.createElement("span");
    spanX.setAttribute("class", "badge");
    spanX.style.cursor = "pointer";
    spanX.innerHTML = "X";
    spanX.onclick = onclick;

    var spanTag = document.createElement("span");
    spanTag.innerHTML = name;

    div.appendChild(spanX);
    div.appendChild(spanTag);

    return div;
}