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

    /**
     * Send XMLHttpRequest to get the milestone.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    getMilestone: function(options, callbackDone, callbackFail) {    
        if (options === undefined) options = {};
        if (options.milestoneId === undefined) {
            throw("Undefined milestone.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/milestones/" + options.milestoneId,
            type: "GET"
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to get the note.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    getNote: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.noteId === undefined) {
            throw("Undefined note.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/notes/" + options.noteId,
            type: "GET"
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to add a note.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    addNote: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.title === undefined) {
            throw("Undefined title.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/notes",
            type: "POST",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to update the note.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    updateNote: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.noteId === undefined) {
            throw("Undefined note.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/notes/" + options.noteId,
            type: "PUT",
            data: options
        })
            .done(callbackDone)
            .fail(callbackFail);
    },

    /**
     * Send XMLHttpRequest to delete the note.
     * @options {Object} dictionary with options.
     * @callbackDone {function} successful callback
     * @callbackFail {function} failure callback
     */
    deleteNote: function(options, callbackDone, callbackFail) {
        if (options === undefined) options = {};
        if (options.noteId === undefined) {
            throw("Undefined note.");
        }
        $.ajax({
            url: "/api/users/" + this.username + "/projects/" +
                 this.projectId + "/notes/" + options.noteId,
            type: "DELETE"
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
                var tags = data["tags"].map(
                        function(item) { return item["name"]; }
                    ).join(", ");
                if (tags === "") {
                    $modal.find("#task-show-tags").html(" ------ ");
                } else {
                    $modal.find("#task-show-tags").html(tags);
                }
                if (data["body"] === "" || data["body"] === null) {
                    $modal.find(".resource-body").text("No description."); 
                } else {
                    $modal.find(".resource-body").text(data["body"]);
                }
            },
            ajaxErrorsHandler
        );
    });

    $("#new-milestone-btn").click(function() {
        var title = $("#milestone-title").val();
        var desc = $("#milestone-desc").val();
        var milestoneId = $("#modal-milestone-edit").data("milestoneid");

        if (milestoneId != "-1") { // update milestone
            project.updateMilestone({
                milestoneId: milestoneId, title: title, desc: desc
            }, function(data, status, xhr) {
                if (title !== "") { // Title have changed.
                    $(".project-milestone[data-milestoneid='" + 
                      milestoneId +"']").find(".milestone-title").text(title); 
                }
                $('#modal-milestone-edit').modal("hide");
            }, ajaxErrorsHandler);
        } else {
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
                        $('#modal-milestone-edit').modal("hide");
                    }, ajaxErrorsHandler);
            }
        }
    });

    $(document).on("click", ".milestone-option-add-task", function() {
        var milestoneId = $(this).parent().parent().parent().data("milestoneid");
        var $modal = $("#modal-task-edit");
        $modal.modal("show");
        $modal.data("milestoneid", milestoneId);
        new TagsPicker({
                input: $("#task-tags-select"),
                output: $("#task-tags-output"),
                list: $("#task-tags"),
                modal: $("#modal-new-tag")
            });
    });

    $(document).on("click", ".task-btn-edit", function() {
        var milestoneId = $(this).parent().parent().parent().data("milestoneid");
        var taskId = $(this).parent().data("taskid");

        // Send request for task info and update modal with task data
        project.getTask({
            taskId: taskId, milestoneId: milestoneId
        },function(data, status, xhr) {
            var $modal = $("#modal-task-edit");
            $modal.modal("show");
            $modal.data("milestoneid", milestoneId);
            $modal.data("taskid", taskId);
            $modal.find("#task-title").val(data["title"]);
            $modal.find("#task-deadline").val(data["deadline"]);
            $modal.find("#task-body").val(data["body"]);
            $modal.find("#task-tags-output").val(
                data["tags"].map(function(item) { 
                    return item["name"]; 
            }).join(","));

            new TagsPicker({
                    input: $("#task-tags-select"),
                    output: $("#task-tags-output"),
                    list: $("#task-tags"),
                    modal: $("#modal-new-tag")
                });

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
        var tags = $("#task-tags-output").val();

        var $milestone = $(".project-milestone[data-milestoneid='" + 
                           milestoneId + "']");

        if (taskId != "-1") { // update the task
            project.updateTask({
                taskId: taskId, milestoneId: milestoneId,
                title: title, body: body, deadline: deadline,
                tags: tags
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
                    milestoneId: milestoneId, tags: tags
                }, function(data, status, xhr) {
                    var uri = xhr.getResponseHeader("Location");
                    var tid = uri.split("/").pop();              
                    
                    $milestone.find(".milestone-tasks").append(
                            createTaskElement(id=tid, title=title, 
                                              complete=false));
                    $('#modal-task-edit').modal("hide");

                    // Send next request for task info
                    // project.getTask({
                    //     taskId: tid, milestoneId: milestoneId
                    // }, function(data, status, xhr) {
                    //     $milestone.find(".milestone-tasks").append(
                    //         createTaskElement(id=data["id"], title=data["title"], 
                    //                           complete=data["complete"]));
                    //     $('#modal-task-edit').modal("hide");
                    // }, ajaxErrorsHandler);

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

    $(document).on("click", ".task-btn-move", function() {
        var taskId = $(this).parent().data("taskid");
        var milestoneId = $(this).closest(".project-milestone").
                          data("milestoneid");
        var $modal = $("#modal-task-move");
        $modal.data("milestoneid", milestoneId);
        $modal.data("taskid", taskId);
        $modal.modal("show");
        return false;
    });

    $("#move-task-btn").click(function() {
        var newMilestoneId = $("#milestone4task-id").val();
        if (newMilestoneId === null) {
            alert("You have not selected any milestone.");
        } else {
            var milestoneId = $("#modal-task-move").data("milestoneid");
            var taskId = $("#modal-task-move").data("taskid");

            if (milestoneId == newMilestoneId) {
                alert("The task is already in this milestone.");
            } else {
                project.updateTask({
                    taskId: taskId, milestoneId: milestoneId,
                    milestone_id: newMilestoneId
                }, function(data, status, xhr) {
                    var $tasksList = $(".project-milestone[data-milestoneid='" + 
                                       newMilestoneId + "']").find(".milestone-tasks");
                    var $task = $(".milestone-task[data-taskid='" + taskId + "']");
                    $task.remove().appendTo($tasksList);
                    $('#modal-task-move').modal("hide");
                }, ajaxErrorsHandler);
            }
        }
    });

    $(document).on("click", ".milestone-option-edit", function() {
        var milestoneId = $(this).closest(".project-milestone").
                                  data("milestoneid");
        project.getMilestone({
            milestoneId: milestoneId
        },function(data, status, xhr) {
            var $modal = $("#modal-milestone-edit");
            $modal.modal("show");
            $modal.data("milestoneid", milestoneId);
            $modal.find("#milestone-title").val(data["title"]);
            $modal.find("#milestone-desc").val(data["desc"]);
        }, ajaxErrorsHandler);

        return false;
    });

    $(document).on("click", ".milestone-option-info", function() {
        var milestoneId = $(this).closest(".project-milestone").
                                  data("milestoneid"); 
        project.getMilestone({milestoneId: milestoneId},
            function(data, status, xhr) {
                var $modal = $("#modal-milestone-show");
                $modal.find("#milestone-show-title").text(data["title"]);
                $modal.find("#milestone-show-desc").text(data["desc"]);
                $modal.modal("show");  
            }, ajaxErrorsHandler);    
        return false;
    });

    $("#add-note").click(function() {
        $("#modal-note-edit").modal("show");
        new TagsPicker({
                input: $("#note-tags-select"),
                output: $("#note-tags-output"),
                list: $("#note-tags"),
                modal: $("#modal-new-tag")
            });
    });

    // Create new note
    $("#new-note-btn").click(function() {
        var title = $("#note-title").val();
        var body = $("#note-body").val();
        var noteId = $("#modal-note-edit").data("noteid");
        var tags = $("#note-tags-output").val();

        if (noteId != "-1") { // update the task
            project.updateNote({
                noteId: noteId, title: title, body: body, tags: tags
            }, function(data, status, xhr) {
                if (title !== "") { // Title have changed.
                    $(".project-note[data-noteid='" + noteId +"']").
                        find(".note-title").text(title); 
                }
                $('#modal-note-edit').modal("hide");
            }, ajaxErrorsHandler);
        } else {
            if (title === "") {
                alert("No title. Please enter title in order to create new note.")
            } else {
                project.addNote({title: title, body: body, tags: tags}, 
                    function(data, status, xhr) {
                        var uri = xhr.getResponseHeader("Location");
                        var nid = uri.split("/").pop();              
                        
                        $("#project-notes-id").append(createNoteElement(
                            {id: nid, title: title, timestamp: moment()}));
                        $('#modal-note-edit').modal("hide");
                    }, ajaxErrorsHandler);
            }
        }
    });

    // Click on the note to show its details
    $(document).on("click", ".project-note", function() {
        var noteId = $(this).data("noteid");
        project.getNote({noteId: noteId}, 
            function(data, status, xhr) {
                var $modal = $("#modal-note-show");
                $modal.modal("show");
                $modal.find("#note-show-main-title").text(data["title"]);
                $modal.find("#note-show-title").text(data["title"]);
                $modal.find("#note-show-timestamp").text(data["timestamp"]);
                if (data["body"] === "" || data["body"] === null) {
                    $modal.find(".resource-body").text("No description."); 
                } else {
                    $modal.find(".resource-body").text(data["body"]);
                }
                var tags = data["tags"].map(function(item) { 
                        return item["name"]; 
                    }).join(", ");
                $modal.find("#note-show-tags").text(tags);
            }, ajaxErrorsHandler);
    });

    $(document).on("click", ".note-btn-edit", function() {
        var noteId = $(this).closest(".project-note").data("noteid");
        project.getNote({noteId: noteId}, 
            function(data, status, xhr) {
                var $modal = $("#modal-note-edit");
                $modal.modal("show");
                $modal.data("noteid", noteId);
                $modal.find("#note-title").val(data["title"]);
                $modal.find("#note-body").val(data["body"]);
                $modal.find("#note-tags-output").val(
                    data["tags"].map(function(item) { 
                        return item["name"]; 
                }).join(","));

                new TagsPicker({
                        input: $("#note-tags-select"),
                        output: $("#note-tags-output"),
                        list: $("#note-tags"),
                        modal: $("#modal-new-tag")
                    });
            }, ajaxErrorsHandler);
        return false;
    });

    $(document).on("click", ".note-btn-remove", function() {
        var noteId = $(this).closest(".project-note").data("noteid");
        if (confirm("Are you sure you want to remove this note?")) {
            var $taskDOM = $(this).parent(); // required in callback
            project.deleteNote({
                noteId: noteId
            },function(data, status, xhr) {
                $taskDOM.remove();
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
    div.innerHTML = "<span class='milestone-title'>" + title + 
                    "</span><div class='arrow arrow-down'></div>";

    var options = document.createElement("ul");
    options.className = "milestone-options";
    options.appendChild(createMilestoneOption("Add Task", "milestone-option-add-task"));
    options.appendChild(createMilestoneOption("Info", "milestone-option-info"));
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
        divCheck = createImgBtn(
            "/static/images/unchecked_checkbox.png",
            "task-btn task-btn-check", "unchecked-checkbox"
        );
    } else {
         divCheck = createImgBtn(
            "/static/images/checked_checkbox.png",
            "task-btn task-btn-check", "checked-checkbox"
        );           
    }
    li.appendChild(span);
    li.appendChild(divCheck);
    li.appendChild(createImgBtn(
        "/static/images/edit-button.png",
        "task-btn task-btn-edit", "edit-task"
    ));
    li.appendChild(createImgBtn(
        "/static/images/remove-button.png",
        "task-btn task-btn-remove", "remove-task"
    ));
    li.appendChild(createImgBtn(
        "/static/images/move-button.png",
        "task-btn task-btn-move", "move-task"
    ));

    return li;
}

/**
 * Create task img.
 * @imgsrc {string} image path
 * @classname {string} class name
 * @alt {string} alt text
 */
function createImgBtn(imgsrc, classname, alt, width, height) {
    if (width === undefined) width = 26;
    if (height === undefined) height = 26;

    var div = document.createElement("div");
    div.className = classname;
    var img = document.createElement("img");
    img.src = imgsrc;
    img.alt = alt;
    img.width = width;
    img.height = height;
    div.appendChild(img);
    return div;
}

/**
 * Create note.
 * @note {object} note objects
 */
function createNoteElement(note) {
    var $li = $("<li/>", {class: "project-note", "data-noteid": note.id});
    var $noteContent = $("<div />", {class: "note-content"});

    $noteContent.append(createImgBtn(
        "/static/images/edit-button.png",
        "note-btn note-btn-edit", "note-edit"
    ));
    $noteContent.append(createImgBtn(
        "/static/images/remove-button.png",
        "note-btn note-btn-remove", "remove-note"
    ));

    // $noteContent.append($("<div />", {class: "note-date", 
    //     text: moment(note.timestamp).format("YYYY-MM-DD HH:mm") }));
    $noteContent.append($("<div />", {class: "note-title", text: note.title}));

    var $noteFooter = $("<div />", {class: "note-footer",
        text: moment(note.timestamp).format("YYYY-MM-DD HH:mm") });
    $noteContent.append($noteFooter);
    $li.append($noteContent);
    return $li;
}

/*******************************************************************************
 MODALs EVENTS
*******************************************************************************/

$("#modal-milestone-edit").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#milestone-title").val("");
    $modal.find("#milestone-desc").val("");
    $modal.data("milestoneid", "-1");
});

$("#modal-task-edit").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#task-title").val("");
    $modal.find("#task-body").val("");
    $modal.find("#task-deadline").val("");
    $modal.data("milestoneid", "-1");
    $modal.data("taskid", "-1");
    $modal.find("#task-tags-output").val("");
    $modal.find("#task-tags").children().not(":first").remove();
});

$("#modal-task-show").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find(".resource-header").find("tr td:last-child").html("");
    $modal.find(".resource-body").html("");
});

$("#modal-note-show").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find(".resource-header").find("tr td:last-child").html("");
    $modal.find(".resource-body").html("");
});

$("#modal-task-move").on("show.bs.modal", function(event) {
    var $modal = $(this);

    var $select = $modal.find('#milestone4task-id');
    $select.empty();
    $select.append("<option disabled selected value='none'>" +
                   "--Select Milestone--</option>");

    var milestoneId = $(this).data("milestoneid");

    // Create list of milestones.
    $(".project-milestone").not(":last").each(function(index) {
        if ($(this).data("milestoneid") != milestoneId) {
            $select.append(
                $("<option></option>").val($(this).data("milestoneid")).
                    html($(this).find(".milestone-title").html())
            );
        }
    });
});

$("#modal-note-edit").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#note-title").val("");
    $modal.find("#note-body").val("");
    $modal.data("noteid", "-1");
    $modal.find("#note-tags-output").val("");
    $modal.find("#note-tags").children().not(":first").remove();
});

$("#modal-new-tag").on("show.bs.modal", function(event) {
    var $modal = $(this);
    $modal.find("#new-tag-name").val("");
});