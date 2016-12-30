/*!
 * E-Mails Iterators
 * - EMailsManager 
 * - SelectManager
 * - SearchManager
 */

/******************************************************************************
 * EMailsManager
 * - iterate over emails
 ******************************************************************************/

function EMailsManager(options) {
    if (options === undefined) options = {};
    if (options.emailsPerPage === undefined) {
        throw("EMailsManager: undefined emails per page");    
    }
    if (options.emailsPerPage < 0) {
        throw("EMailsManager: emails per page is negative");    
    }
    if (options.caching === undefined) {
        this.caching = false;
    } else {
        this.caching = options.caching;
    }
    this.emailsPerPage = Math.ceil(options.emailsPerPage);
    this.requestInProgress = false;
    this.callbacks = {
        onLoad: undefined,
        onLoaded: undefined,
        onUpdate: undefined,
        onUpdated: undefined
    };
    this.cache = {};
    this.source = undefined;
}

EMailsManager.prototype.setSource = function(source) {
    this.source = source;
    this.page = 0;
}

EMailsManager.prototype.updateSource = function() {
    if (this.source === undefined) {
        throw("Undefined source of e-mails.");
    }  
    if (this.callbacks.onUpdate !== undefined) {
        this.callbacks.onUpdate();
    }
    this.source.update(this.callbacks.onUpdated);
}

EMailsManager.prototype.getCurrentPage = function() {
    return this.page;
}

EMailsManager.prototype.getPageSize = function() {
    return this.emailsPerPage;
}

EMailsManager.prototype.getCurrentMailbox = function() {
    return this.source.mailbox;
}

EMailsManager.prototype.isUid = function() {
    return this.source.is_uid;
}

EMailsManager.prototype.on = function(event, callback) {
    this.callbacks[event] = callback;
};

EMailsManager.prototype.nextPage = function() {
    if (this.hasNextPage()) {
        this.loadEMails(this.getCurrentPage() + 1);
    }
};

EMailsManager.prototype.prevPage = function() {
    if (this.hasPrevPage()) {
        this.loadEMails(this.getCurrentPage() - 1);
    }
};

EMailsManager.prototype.toCacheId = function(id) {
    return ("" + id);
};

EMailsManager.prototype.loadEMails = function(page) {
    if (!this.requestInProgress) { 
        this.requestInProgress = true;
        
        if (this.callbacks.onLoad !== undefined) {
            this.callbacks.onLoad();
        }

        var ids = this.getIds(page);
        var new_ids = ids;
        if (this.caching) { // load only new e-mails when caching is on
            new_ids = [];
            for (var i = 0; i < ids.length; i++) {
                if (!(this.toCacheId(ids[i]) in this.cache)) {
                    new_ids.push(ids[i]);
                }
            }
        } 

        if (new_ids.length > 0) {
            var self = this;
            var params = {
                ids: new_ids.join(","),
                mailbox: this.getCurrentMailbox(),
                uid: this.isUid(),
                callback: function(response) {
                    if (response.status == "OK") {
                        self.page = page;
                        var data = response.data;
                        if (self.caching) {
                            for (var i = 0; i < data.length; i++) {
                                self.cache[self.toCacheId(data[i]["id"])] = data[i];
                            }
                        }
                    }
                    if (self.callbacks.onLoaded !== undefined) {
                        if (response.status == "OK") {
                            // Update response which contains only new_ids.
                            // Append ids which were cached.
                            if (this.catching) {
                                for (var i = 0; i < ids.length; i++) {
                                    if (!(self.toCacheId(ids[i]) in new_ids)) {
                                        response.data.push(
                                                self.cache[self.toCacheId(ids[i])]
                                            );
                                    }
                                }
                            }
                        }
                        self.callbacks.onLoaded(response);
                    }
                    self.requestInProgress = false;
                }
            };
            getEMailsHeaders(params);    
        } else { // no need to load new e-mails
            this.page = page;
            if (this.callbacks.onLoaded !== undefined) {
                // Create response. Callback should not see the difference.
                var response = {};
                response.status = "OK";
                response.data = [];
                for (var i = 0; i < ids.length; i++) {
                    response.data.push(this.cache[this.toCacheId(ids[i])]);
                }
                this.callbacks.onLoaded(response);
            }
            this.requestInProgress = false;
        }  
    } else {
        alert("E-mails are being loaded. Please wait a second with " +
              "your next request.");
    }     
};

EMailsManager.prototype.hasNextPage = function() {
    var ids = this.source.getIds();
    if (ids === undefined || ids.length === 0) {
        return false;
    }
    var page = this.getCurrentPage();
    var pageSize = this.getPageSize();
    if (ids.length - page*pageSize > 0) {
        return true;
    } 
    return false;
};

EMailsManager.prototype.hasPrevPage = function() {
    var ids = this.source.getIds();
    var page = this.getCurrentPage();
    if (ids === undefined || ids.length === 0 || page < 2) {
        return false;
    }
    return true;
};

EMailsManager.prototype.getIds = function(page) {
    var ids = this.source.getIds();
    if (ids === undefined) {
        return undefined;
    }
    var pageSize = this.getPageSize();
    return (ids.slice((page-1)*pageSize, page*pageSize));
};

EMailsManager.prototype.getEMailsCount = function() {
    var ids = this.source.getIds();
    if (ids === undefined) {
        return 0;
    } else {
        return ids.length;
    }
};


/******************************************************************************
 * SelectSource
 * - get emails ids from select
 ******************************************************************************/

function SelectSource(options) { 
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw("SelectSource: undefined mailbox"); 
    } 
    this.mailbox = options.mailbox;
    this.is_uid = false;
    if (options.uid !== undefined) {
        this.is_uid = options.uid;
    }
}

SelectSource.prototype.update = function(callback) {
    var self = this;
    getEMailsList({
        mailbox: self.mailbox,
        uid: self.is_uid,
        callback: function(response) {
            if (response.status == "OK") {
                self.ids = response.data;
                self.ids.reverse();
            }
            if (callback !== undefined) {
                callback(response);
            }
        }
    });
};

SelectSource.prototype.getIds = function() {
    return (this.ids);
}

/******************************************************************************
 * SearchSource
 * - get e-mails ids from search
 ******************************************************************************/

function SearchSource(options) { 
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw("SearchSource: undefined mailbox"); 
    }
    this.mailbox = options.mailbox;
    if (options.criteria === undefined) {
        throw("SearchSource: undefined criteria"); 
    }
    this.criteria = []; // make copy
    for (var i = 0; i < options.criteria.length; i++) {
        this.criteria.push({
            key: options.criteria[i].key,
            value: options.criteria[i].value,
            decode: options.criteria[i].decode
        });
    }
    this.is_uid = false;
    if (options.uid !== undefined) {
        this.is_uid = options.uid;
    }
}

SearchSource.prototype.update = function(callback) {
    var self = this;
    searchEMails({
            mailbox: self.mailbox,
            criteria: self.criteria,
            uid: self.is_uid,
            callback: function(response) {
                if (response.status == "OK") {
                    self.ids = response.data;
                    self.ids.reverse();
                }
                if (callback !== undefined) {
                    callback(response);
                }  
            }
        });
};

SearchSource.prototype.getIds = function() {
    return (this.ids);
}