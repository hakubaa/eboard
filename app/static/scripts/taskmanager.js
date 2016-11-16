function TaskManager(tasks, table, config) {
    if (tasks === undefined) tasks = [];
    this.tasks = tasks;
    this.table = table;
    this.config = config;
    this.onedit = undefined;
}

TaskManager.prototype.count = function() {
    return this.tasks.length;
};

TaskManager.prototype.contains = function(spec) {
    for (var i = 0; i < this.tasks.length; i++) {
        if (isPartOf(this.tasks[i], spec)) {
            return true;
        }
    }
    return false;
    
};

TaskManager.prototype.insert = function(task) {
    this.tasks.push(task);
}

TaskManager.prototype.find = function(spec) {
    if (spec === undefined) return this.tasks;

    var result = [];
    for (var i = 0; i < this.tasks.length; i++) {
        if (isPartOf(this.tasks[i], spec)) {
            result.push(this.tasks[i]);
        }   
    }
    return result;
}

TaskManager.prototype.findOne = function(spec) {
    if (spec === undefined) return this.tasks[0];
    for (var i = 0; i < this.tasks.length; i++) {
        if (isPartOf(this.tasks[i], spec)) {
            return this.tasks[i];
        }   
    }
    return null;
}

TaskManager.prototype.remove = function(spec) {
    var tasks2remove = this.find(spec).map(
        function(obj) { 
            return this.tasks.indexOf(obj); 
        }, this);
    for (var i = tasks2remove.length - 1; i >= 0; i--) {
        this.tasks.splice(tasks2remove[i], 1);
    }
    return tasks2remove.length;
}

TaskManager.prototype.sort = function(sortSpec) {
    /*
     * sort({ "field1": 1, "field2": -1 });
     * 1 - ascending, -1 descending
     */
    this.tasks.sort(dynamicSortMultiple.apply(this, 
        Object.keys(sortSpec).map(function(value, index) {
            return ((sortSpec[[value]] < 0 ? "-" : "") + value);
        }, this)));
    return this;
}

TaskManager.prototype.refreshDOM = function(spec) {
    if (!this.table) return false;

    var tasks = this.find(spec);
    var manager = this;

    // Remove current tasks' rows
    $(this.table).empty();

    // Add new tasks
    for (var i = 0; i < tasks.length; i++) {

        var deadline = moment(tasks[i].deadline, "YYYY-MM-DD HH:mm:ss")

        var tr = document.createElement("tr");
            tr.setAttribute("class", "task-record " + 
            ( moment().isAfter(deadline) && tasks[i].status.name == "active" ? 
            "delayed" : "") + " " + tasks[i].status.name);
        tr.setAttribute("data-task-id", tasks[i].id);

        var tdHTML = [tasks[i].title + " (id: " + tasks[i].id + ")", 
                deadline.format("LLL") + " (" + moment().to(deadline) + ")", // tasks[i].notes, 
                tasks[i].tags.map(function(obj) { return obj.name; }, this).join(", "),
                tasks[i].project ? "<a href='project/" + tasks[i].project.id + "'>" + tasks[i].project.name + "</a>" : ""];
        var td;
        for(var j = 0; j < tdHTML.length; j++) {
            td = document.createElement("td");
            td.innerHTML = tdHTML[j];
            tr.appendChild(td);
        } 

        var select = document.createElement("select");
        select.className = "form-control input-sm ignore";

        var taskKeys = Object.keys(this.config.taskStatuses);
        for (var j = 0; j < taskKeys.length; j++) {
            var option = document.createElement("option");
            option.value = taskKeys[j];
            option.innerHTML = this.config.taskStatuses[taskKeys[j]];
            if (tasks[i].status.name == taskKeys[j]) {
                option.selected = true;
            }
            select.appendChild(option);
        }

        // Stop propagation onclick event on select. When user changes task's
        // status, propagation causes refreshment of the task info.
        select.onclick = function(event) {
            event.stopPropagation();   
        }
        select.onchange = (function() {
            var taskId = manager.tasks[i].id;
            var status = manager.tasks[i].status.name;
            var taskRow = tr;

            return function(event) {
                $.ajax({
                    url: "project/task/status",
                    type: "POST",
                    contentType: "application/json; charset=utf-8",
                    data: JSON.stringify({ 
                        taskid: taskId, 
                        status: this.value 
                    }),
                    cache: false,
                    dataType: "json",
                    success: function(response) {
                        if (response.status == "success") {
                            var task = manager.findOne({ "id": response.data.id });
                            if (task) {
                                task.status.name = response.data.status;
                                task.status.label = manager.config.taskStatuses[response.data.status]; 
                                $(taskRow).removeClass(status);
                                $(taskRow).addClass(response.data.status);
                                if (response.data.status != "active") {
                                    $(taskRow).removeClass("delayed");
                                } else {
                                    if (task.daysleft < 0) {
                                        $(taskRow).addClass("delayed");
                                    }
                                }
                                status = response.data.status;
                            } 
                        }
                    }
                });   
            };
        })();

        td = document.createElement("td");
        td.appendChild(select);
        tr.appendChild(td);

        td = document.createElement("td");
        var editLink = document.createElement("a");
        editLink.href = "tasks/edit/" + tasks[i].id;
        editLink.innerHTML = "<img src=" + this.config.editImg +" width='20' height='20'>";
        td.className = "buttonImg";
        td.appendChild(editLink);
        tr.appendChild(td);

        var removeButton = document.createElement("img");
        removeButton.src = this.config.removeImg;
        removeButton.width = "20";
        removeButton.height = "20";
        removeButton.style.cursor = "pointer";
        // button.type = "button";
        // button.className = "btn btn-default btn-sm";
        // button.innerHTML = "X";
        removeButton.onclick = (function() {
            var taskId = manager.tasks[i].id;
            return function(event) {
                if (confirm("Are your sure you want to remove this task?")) {
                    var taskRow = this.parentNode.parentNode;
                    $.ajax({
                        url: "/eboard/tasks/remove",
                        type: "POST",
                        contentType: "application/json; charset=utf-8",
                        data: JSON.stringify({ 
                            taskid: taskId
                        }),
                        cache: false,
                        dataType: "json",
                        success: function(response) {
                            if (response.status == "success") {
                                manager.remove({"id": response.data.taskid});
                                taskRow.parentNode.removeChild(taskRow);
                            }
                        }
                    });
                }
            };
        })();
        td = document.createElement("td");
        td.className = "buttonImg";
        td.appendChild(removeButton);
        tr.appendChild(td);

        this.table.appendChild(tr);    
    }
    return true;   
}