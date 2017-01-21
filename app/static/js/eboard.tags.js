/**
 * Tags Manager.
 */
function TagsPicker(config) {
    this.output = config.output; 
    this.input = config.input;
    this.list = config.list;
    this.modal = config.modal;

    this.initOutputAndList();
    this.initInput();
}

/**
 * Adjust list of tags with output element.
 */
TagsPicker.prototype.initOutputAndList = function() {
    var tags = this.readTags();
    this.list.not(":first").remove();
    for (var i = 0; i < tags.length; i++) {
        var $li = $("<li></li>", {class: "list-group-item tag-selected"});
        var $tag = createTagElement(tags[i], this.createTagCallback(tags[i]));
        $li.append($tag);
        this.list.append($li);
    }
};

/**
 * Init input with tags. Send request to server for tags.
 */
TagsPicker.prototype.initInput = function() {
    var self = this;
    $.ajax({url: "/api/tags", type: "GET"})
        .done(function(data, status, xhr) {
            self.input.empty();
            self.input.append("<option disabled selected value='none'>" +
                       "--Select Tag--</option>");
            self.input.append("<option value='new'>New Tag</option>");
            for (var i = 0; i < data.length; i++) {
                self.input.append(
                    $("<option></option>").val(data[i].id).html(data[i].name)
                );
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            alert("ERROR: Unable to load tags.");
        });  

    this.input.change(function() {
        var tagId = $(this).val();
        var tagName = $(this).find("option:selected").text();

        if (tagId === "new") {
            self.modal.modal("show");
            self.modal.data("tagslistid", self.input.attr("id"));
        } else {
            self.addTag(tagName);
        }
        $(this).val("none");
   });       
};


/**
 * Add tag element to tags list.
 */
TagsPicker.prototype.addTag = function(name) {
    var tags = this.readTags();
    if (tags.indexOf(name) < 0) {
        // Create DOM
        var $li = $("<li></li>", {class: "list-group-item tag-selected"});
        var self = this;
        $li.append(createTagElement(name, this.createTagCallback(name)));
        this.list.append($li);

        // Save to output.
        tags.push(name);
        this.saveTags(tags);
    }
};

/**
 * Create callback to remove tags.
 */
TagsPicker.prototype.createTagCallback = function(name) {
    var self = this;
    return function() {
        self.removeTag(name);
    };
};

/**
 * Remove tag from output and list.
 */
TagsPicker.prototype.removeTag = function(name) {
    var tags = this.readTags();
    var tagIndex = tags.indexOf(name);
    if (tagIndex >= 0) {
        // Remove from output
        tags.splice(tagIndex, 1);
        this.saveTags(tags);

        // Remove from document
        var $tag = this.findTag(name);
        $tag.remove();  
    }
};

/**
 * Find tag in the list.
 */
TagsPicker.prototype.findTag = function(name) {
    var $tag = this.list.find(".tag-name:contains('" + name + "')").
                   closest("li");
    return $tag;
};

/**
 * Read tags from output.
 */
TagsPicker.prototype.readTags = function() {
    if (this.output.val() === "") {
        return [];
    } 
    return this.output.val().split(",");   
};

/**
 * Save tags to output.
 */
TagsPicker.prototype.saveTags = function(tags) {
    this.output.val(tags.join());
};


$("#new-tag-btn").click(function(event) {
    var tagName = $("#new-tag-name").val();
    if (tagName) {
        if (!/^[a-zA-Z0-9\s_]+$/.test(tagName)) {
            alert("Not allowed signs. Please use only letters, numbers " +
                  "and following signs: space, underscore.");
        } else {                             
            $.ajax({url: "/api/tags/" + tagName, type: "PUT"})
                .done(function(data, status, xhr) { 
                    var selectId = "#" + $("#modal-new-tag").data("tagslistid");
                    $(selectId).append(
                        $("<option></option>").val(data.id).html(data.name)
                    );
                    $("#modal-new-tag").modal("hide");
                })
                .fail(function(jqXHR, textStatus, errorThrown) { 
                    alert("Unable to create new tag.");
                });
        }
    } else {
        alert("Tag name's field is empty. Please enter valid tag name.");
    }  
});

function createTagElement(name, onclick) {
    var $div = $("<div></div>");
    var $spanX = $("<span></span>", {class: "badge", text: "X"});
    $spanX.css("cursor", "pointer");
    $spanX.click(onclick);
    var $spanTag = $("<span class='tag-name'>" + name + "</span>");
    $div.append($spanX);
    $div.append($spanTag);
    return $div;
}