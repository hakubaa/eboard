function TagsPicker(config) {
    this.tags = config.tags; // possible tags to select
    this.selected = []; // selected tags
    this.outputElement = config.outputElement; 
    this.selectElement = config.selectElement;
    this.onnewtag = config.onnewtag;
    this.onselect = config.onselect;
    this.onclear = config.onclear;
    this.active = false;

    if (this.selectElement) {
        var option;
        option = document.createElement("option");
        option.innerHTML = "-- Select Tag --";
        option.value = "no-tag";
        option.setAttribute("disabled", true);
        option.setAttribute("selected", true);
        this.selectElement.appendChild(option);

        option = document.createElement("option");
        option.value = "new-tag";
        option.innerHTML = "-- New Tag --";
        this.selectElement.appendChild(option);
        
        for (var i = 0; i < this.tags.length; i++) {
            option = document.createElement("option");
            option.value = this.tags[i].id;
            option.innerHTML = this.tags[i].name;
            this.selectElement.appendChild(option);
        }

        var self = this;
        this.selectElement.onchange = function(event) {
            var tagValue = event.target.value;
            if (tagValue == "new-tag") {
                if (self.onnewtag) self.onnewtag(self);
            } else if (tagValue != "no-tag") {
                self.select(tagValue);
            }
        }
    }
}

TagsPicker.prototype.isActive = function() {
    return this.active;
}

TagsPicker.prototype.setActive = function(active) {
    this.active = active;
}

TagsPicker.prototype.writeOutput = function() {
    if (this.outputElement) {
        this.outputElement.value = JSON.stringify(this.selected);
        return true;
    }
    return false;
}

TagsPicker.prototype.indexOf = function(id) {
    for (var i = 0; i < this.tags.length; i++) {
        if (this.tags[i].id == id) {
            return i;
        }
    }
    return -1;
}

TagsPicker.prototype.containTag = function(id) {
    return !(this.indexOf(String(id)) < 0);
};

TagsPicker.prototype.addTag = function(id, name, select) {
    if (select === undefined) select = false;

    if (!this.containTag(id)) {
        this.tags.push({ id: String(id), name: name});

        var option = document.createElement("option");
        option.value = id;
        option.innerHTML = name;
        this.selectElement.appendChild(option);

        if (select) {
            this.select(id);
            option.setAttribute("selected", true);
        }
        return true;
    }
    return false;
};

TagsPicker.prototype.getTag = function(id) {
    var index = this.indexOf(id);
    if (index < 0) {
        return null;
    } else {
        return this.tags[index];
    }
}

TagsPicker.prototype.removeTag = function(id) {
    if (this.containTag(id)) {
        this.tags.splice(this.indexOf(id), 1);  
        return true;
    }
    return false;
};

TagsPicker.prototype.select = function(id) {
    if (this.containTag(id) && !this.isSelected(id)) {
        this.selected.push(String(id));
        this.writeOutput();
        if (this.onselect) {
            var tag = this.getTag(id);
            this.onselect(tag.id, tag.name);
        }
        return true;
    }
    return false;
}

TagsPicker.prototype.unselect = function(id) {
    if (this.isSelected(id)) {
        this.selected.splice(this.selected.indexOf(id), 1);
        this.writeOutput();
        return true;
    }
    return false;
}

TagsPicker.prototype.isSelected = function(id) {
    return !(this.selected.indexOf(String(id)) < 0);
}

TagsPicker.prototype.clear = function() {
    this.selected = [];
    this.writeOutput();
    this.onclear();
}