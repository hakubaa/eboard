var project = {

    /**
     * Send XMLHttpRequest for information about project.
     * @param {Object} params Dictionary with parameters.
     */
    init: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.username === undefined) {
            throw("Undefined username.");
        }
        if (options.projectId === undefined) {
            throw("Undefined project id.");
        }

        this.username = options.username;
        this.projectId = options.projectId;

        $.ajax({
            url: "/api/users/" + options.username + "/projects/" + 
                 options.projectId + "?with_tasks=T",
            type: "GET"
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to create milestone.
     * @param {Object} params Dictionary with parameters.
     */
    addMilestone: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.title === undefined) {
            throw("Undefined title.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" + 
                 this.projectId + "/milestones",
            type: "POST",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    }
};

/**
 * Initialize UI including events handlers.
 */
function initUI() {

    // Click on the milestone label to show tasks
    $(document).on("click", ".milestone-label", function() {
        $(this).siblings().filter(".milestone-tasks").toggle();
        $(this).siblings().filter(".milestone-options").toggle();
        $(this).find(".arrow").toggleClass("arrow-down arrow-up");
    });    

    // Click on the note to show its details
    $(document).on("click", ".project-note", function() {
        alert($(this).data("note-id"));
    });

    $("#new-milestone-btn").click(function() {
        var title = $("#milestone-title").val();
        var desc = $("#milestone-desc").val();

        if (title === "") {
            alert("Empty title. Please enter the title to create a milestone.");
        } else {
            project.addMilestone({
                    title: title, desc: desc
                }, function(data, status, xhr) {
                    var uri = xhr.getResponseHeader("Location");
                    var mid = uri.split("/").pop(); // get id of milestone
                    var $milestone = $(createMilestoneElement(mid, title));
                    $("#project-plan-id").find("li:last").before($milestone);
                    $('#modal-milestone').modal("hide");
                });
        }
    });
}


/*******************************************************************************
 DOM CREATORS
*******************************************************************************/

/**
 * Create project.
 * @id {integer} milestone id
 * @title {string} milestone title
 */
function showProject(project) {
    // Add milestones and tasks
    var $project = $("#project-plan-id");
    $project.children().not(":last").remove();

    var milestones = project.milestones.sort(function(x, y) {
        return x.position - y.position;
    });
    for (var i = 0; i < milestones.length; i++) {
        var $milestone = $(createMilestoneElement(id=milestones[i].id, 
            title=milestones[i].title));
        var $tasks = $milestone.find(".milestone-tasks");

        var tasks_data = milestones[i].tasks.sort(function(x, y) {
            return moment(x.deadline) < moment(y.deadline);
        });
        
        for (var j = 0; j < tasks_data.length; j++) {
            $tasks.append(createTaskElement(id=tasks_data[j].id,
                title=tasks_data[j].title, active=true));
        }

        $project.find("li:last").before($milestone);
    }

    // Add notes
    var $notes = $("#project-notes-id");
    $notes.empty();

    var notes_data = project.notes.sort(function(x, y) {
        return moment(x.timestamp) < moment(y.timestamp);
    });
    for (var i = 0; i < notes_data.length; i++) {
        $notes.append(createNoteElement(notes_data[i]));
    }
}

/**
 * Create milestone element (li).
 * @id {integer} milestone id
 * @title {string} milestone title
 */
function createMilestoneElement(id, title) {
    var li = document.createElement("li");
    li.className = "project-milestone";
    li.setAttribute("data-milestoneid", id);

    var div = document.createElement("div");
    div.className = "milestone-label";
    div.innerHTML = "<span class='milestone-title'>" + title + "</span><div class='arrow arrow-down'></div>";

    var options = document.createElement("ul");
    options.className = "milestone-options";
    options.appendChild(createMilestoneOption("Add Task", "milestone-option-add-task"));
    options.appendChild(createMilestoneOption("Move Up", "milestone-option-move-up"));
    options.appendChild(createMilestoneOption("Move Down", "milestone-option-move-down"));
    options.appendChild(createMilestoneOption("Edit", "milestone-option-edit"));
    options.appendChild(createMilestoneOption("Remove", "milestone-option-remove"));

    var tasks = document.createElement("ul");
    tasks.className = "milestone-tasks";

    li.appendChild(div);
    li.appendChild(options);
    li.appendChild(tasks);

    return li;
}

/**
 * Create milestone option (li).
 * @id {integer} milestone id
 * @title {string} milestone title
 */
function createMilestoneOption(name, classname) {
    var li = document.createElement("li");
    li.className = "milestone-option";
    var div = document.createElement("div");
    div.className = classname;
    div.innerHTML = name;
    li.appendChild(div);
    return li;
}

/**
 * Create task element.
 * @id {integer} milestone id
 * @title {string} milestone title
 * @active {bool} flag indicating whether task is still active
 */
function createTaskElement(id, title, active) {
    var li = document.createElement("li");
    li.className = "milestone-task";
    li.setAttribute("data-task-id", id);

    var span = document.createElement("span");
    span.className = "task-title";
    span.innerHTML = title;

    var divCheck;
    if (active) {
        divCheck = createTaskImg(
            "/static/images/unchecked_checkbox.png",
            "task-btn-check", "unchecked-checkbox"
        );
    } else {
         divCheck = createTaskImg(
            "/static/images/checked_checkbox.png",
            "task-btn-check", "checked-checkbox"
        );           
    }
    li.appendChild(span);
    li.appendChild(divCheck);
    li.appendChild(createTaskImg(
        "/static/images/edit-button.png",
        "task-btn-edit", "edit-task"
    ));
    li.appendChild(createTaskImg(
        "/static/images/remove-button.png",
        "task-btn-remove", "remove-task"
    ));
    li.appendChild(createTaskImg(
        "/static/images/move-button.png",
        "task-btn-move", "move-task"
    ));

    return li;
}

/**
 * Create task img.
 * @imgsrc {string} image path
 * @classname {string} class name
 * @alt {string} alt text
 */
function createTaskImg(imgsrc, classname, alt) {
    var div = document.createElement("div");
    div.className = "task-btn " + classname;
    var img = document.createElement("img");
    img.src = imgsrc;
    img.alt = alt;
    img.width = "26";
    img.height = "26";
    div.appendChild(img);
    return div;
}

/**
 * Create note.
 * @note {object} note objects
 */
function createNoteElement(note) {
    var $li = $("<li/>", {class: "project-note", "data-note-id": note.id});
    var $noteContent = $("<div />", {class: "note-content"})
    $noteContent.append($("<div />", {class: "note-date", 
        text: moment(note.timestamp).format("YYYY-MM-DD HH:mm") }));
    $noteContent.append($("<div />", {class: "note-title", text: note.title}));
    $li.append($noteContent);
    return $li;
}

/*******************************************************************************
 MILESTONES EVENTS
*******************************************************************************/

$("#modal-milestone").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#milestone-title").val("");
    $modal.find("#milestone-desc").val("");
});