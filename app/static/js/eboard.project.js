var project = {

    /**
     * Send XMLHttpRequest for information about project.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
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
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
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
    },

    /**
     * Send XMLHttpRequest to create new task.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    addTask: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.title === undefined) {
            throw("Undefined title.");
        }
        if (options.deadline === undefined) {
            throw("Undefined deadline.");
        }
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId + 
                 "/tasks",
            type: "POST",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to update a task.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    updateTask: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.taskId === undefined) {
            throw("Undefined task.");
        }
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId +
                 "/tasks/" + options.taskId,
            type: "PUT",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to get the task;
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    getTask: function(options, callbackDone, callbackFail) {    
        if (options === undefined) options = {};
        if (options.taskId === undefined) {
            throw("Undefined task.");
        }
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId + 
                 "/tasks/" + options.taskId,
            type: "GET"
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to delete the task.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    deleteTask: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.taskId === undefined) {
            throw("Undefined task.");
        }
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId + 
                 "/tasks/" + options.taskId,
            type: "DELETE"
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to update the milestone.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    updateMilestone: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId,
            type: "PUT",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to move milestone within the project.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    moveMilestone: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        if (options.after === undefined && options.before === undefined) {
            throw("Undefined reference milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId +
                 "/position",
            type: "POST",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to delete the milestone.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    deleteMilestone: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId,
            type: "DELETE"
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

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

    $(document).on("click", ".milestone-task", function() {
        var taskId = $(this).data("taskid");
        var milestoneId = $(this).parent().parent().data("milestoneid");
        
        var $modal = $("#modal-task-show");

        $modal.find("#task-show-main-title").html("Loading ...");
        $modal.modal("show");

        project.getTask(
            {taskId: taskId, milestoneId: milestoneId},
            function(data, status, xhr) {
                $modal.find("#task-show-main-title").html(data["title"]);
                $modal.find("#task-show-title").html(data["title"]);
                $modal.find("#task-show-deadline").html(data["deadline"] + 
                    " (" + data["daysleft"] + " day(s) left)");
                if (parseInt(data["daysleft"]) < 0) {
                    $modal.find("#task-show-deadline").css("color", "red");   
                } else {
                    $modal.find("#task-show-deadline").css("color", "green");   
                }
                if (data["complete"]) {
                    $modal.find("#task-show-complete").html("Yes");
                } else {
                    $modal.find("#task-show-complete").html("No"); 
                }
                if (data["active"]) {
                    $modal.find("#task-show-active").html("Yes");
                } else {
                    $modal.find("#task-show-active").html("No");
                }
                $modal.find("#task-show-created").html(data["created"]);
                // $modal.find("#task-show-importance").html(data["importance"]);
                // $modal.find("#task-show-urgency").html(data["urgency"]);
                if (data["body"] === "" || data["body"] === null) {
                    $modal.find("#task-show-body").text("No description."); 
                } else {
                    $modal.find("#task-show-body").text(data["body"]);
                }
            },
            ajaxErrorsHandler
        );
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
                }, ajaxErrorsHandler);
        }
    });

    $(document).on("click", ".milestone-option-add-task", function() {
        var milestoneId = $(this).parent().parent().parent().data("milestoneid");
        var $modal = $("#modal-task-edit");
        $modal.data("milestoneid", milestoneId);
        $modal.modal("show");
    });

    $(document).on("click", ".task-btn-edit", function() {
        var milestoneId = $(this).parent().parent().parent().data("milestoneid");
        var taskId = $(this).parent().data("taskid");

        // Send request for task info and update modal with task data
        project.getTask({
            taskId: taskId, milestoneId: milestoneId
        },function(data, status, xhr) {
            var $modal = $("#modal-task-edit");
            $modal.data("milestoneid", milestoneId);
            $modal.data("taskid", taskId);
            $modal.find("#task-title").val(data["title"]);
            $modal.find("#task-deadline").val(data["deadline"]);
            $modal.find("#task-body").val(data["body"]);
            $modal.modal("show");
        }, ajaxErrorsHandler);

        return false;
    });

    $(document).on("click", ".task-btn-remove", function() {
        var milestoneId = $(this).parent().parent().parent().data("milestoneid");
        var taskId = $(this).parent().data("taskid");

        if (confirm("Are you sure you want to remove this task?")) {
            // Send request to delete task.
            var $taskDOM = $(this).parent(); // required in callback
            project.deleteTask({
                taskId: taskId, milestoneId: milestoneId
            },function(data, status, xhr) {
                $taskDOM.remove();
            }, ajaxErrorsHandler);
        }

        return false;
    });

    $(document).on("click", ".task-btn-check", function() {
        var isComplete = $(this).parent().data("complete");
        var taskId = $(this).parent().data("taskid");
        var milestoneId = $(this).closest(".project-milestone").
                          data("milestoneid");

        var $self = $(this);
        project.updateTask({
            milestoneId: milestoneId, taskId: taskId,
            complete: !isComplete
        }, function(data, status, xhr) {
            if (!isComplete) {
                $self.find("img").attr("src", 
                    "/static/images/checked_checkbox.png");
            } else {
                $self.find("img").attr("src", 
                    "/static/images/unchecked_checkbox.png"); 
            }
            $self.parent().data("complete", !isComplete);
        }, ajaxErrorsHandler);

        return false;
    });

    $("#new-task-btn").click(function() {
        var title = $("#task-title").val();
        var body = $("#task-body").val();
        var deadline = $("#task-deadline").val();
        var milestoneId = $("#modal-task-edit").data("milestoneid");
        var taskId = $("#modal-task-edit").data("taskid");

        var $milestone = $(".project-milestone[data-milestoneid='" + 
                           milestoneId + "']");

        if (taskId !== -1) { // update the task
            project.updateTask({
                taskId: taskId, milestoneId: milestoneId,
                title: title, body: body, deadline: deadline
            }, function(data, status, xhr) {
                if (title !== "") { // Title have changed.
                    $milestone.find("li[data-taskid='" + taskId +"']").
                        find(".task-title").text(title); 
                }
                $('#modal-task-edit').modal("hide");
            }, ajaxErrorsHandler);
        } else { // create new task
            if (title === "" || deadline === "") {
                alert("Empty title and/or deadline. Title and deadline " +
                      "are required.");
            } else {
                project.addTask({
                    title: title, body: body, deadline: deadline,
                    milestoneId: milestoneId
                }, function(data, status, xhr) {
                    var uri = xhr.getResponseHeader("Location");
                    var tid = uri.split("/").pop();              
                    
                    // Send next request for task info
                    project.getTask({
                        taskId: tid, milestoneId: milestoneId
                    }, function(data, status, xhr) {
                        $milestone.find(".milestone-tasks").append(
                            createTaskElement(id=data["id"], title=data["title"], 
                                              complete=data["complete"]));
                        $('#modal-task-edit').modal("hide");
                    }, ajaxErrorsHandler);

                }, ajaxErrorsHandler);
            }
        }
    });

    $(document).on("click", ".milestone-option-move-up", function() {
        var $milestone = $(this).closest(".project-milestone");
        var $prevMilestone = $milestone.prev();
        if ($prevMilestone.length === 1) {
            project.moveMilestone({
                milestoneId: $milestone.data("milestoneid"),
                before: $prevMilestone.data("milestoneid")
            }, function(data, status, xhr) {
                $milestone.insertBefore($prevMilestone); 
            }, ajaxErrorsHandler);
        }
        return false;
    });

    $(document).on("click", ".milestone-option-move-down", function() {
        var $milestone = $(this).closest(".project-milestone");
        var $nextMilestone = $milestone.next();
        if ($nextMilestone.length === 1 
                        && !$nextMilestone.hasClass("project-extra-options")) {
            project.moveMilestone({
                milestoneId: $milestone.data("milestoneid"),
                after: $nextMilestone.data("milestoneid")
            }, function(data, status, xhr) {
                $milestone.insertAfter($nextMilestone); 
            }, ajaxErrorsHandler);
               
        }
        return false;
    });

    $(document).on("click", ".milestone-option-remove", function() {
        var $milestone = $(this).closest(".project-milestone");
        if (confirm("Are you sure you want to remove this milestone?")) {
            project.deleteMilestone({
                milestoneId: $milestone.data("milestoneid")
            }, function(data, status, xhr) {
                $milestone.remove();
            }, ajaxErrorsHandler);
        }
        return false;    
    });
}

function ajaxErrorsHandler(jqXHR, textStatus, errorThrown) {
    var status = "ERROR";
    if (textStatus !== null) status = textStatus.toUpperCase();
    alert(status + ": " + errorThrown);  
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
                title=tasks_data[j].title, complete=tasks_data[j].complete));
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
 * @complete {bool} flag indicating whether task is complete
 */
function createTaskElement(id, title, complete) {
    var li = document.createElement("li");
    li.className = "milestone-task";
    li.setAttribute("data-taskid", id);
    li.setAttribute("data-complete", complete);

    var span = document.createElement("span");
    span.className = "task-title";
    span.innerHTML = title;

    var divCheck;
    if (!complete) {
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
 MODALs EVENTS
*******************************************************************************/

$("#modal-milestone").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#milestone-title").val("");
    $modal.find("#milestone-desc").val("");
});

$("#modal-task-add").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#task-title").val("");
    $modal.find("#task-body").val("");
    $modal.find("#task-deadline").val("");
    $modal.data("milestoneid", "-1");
    $modal.data("taskid", "-1");
});

$("#modal-task-show").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#task-show-header").find("tr td:last-child").html("");
    $modal.find("#task-show-body").html("");
});