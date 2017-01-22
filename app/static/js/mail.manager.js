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

EMailsManager.prototype.getCurrentPageInfo = function() {
    var pageSize = this.getPageSize();
    var page = this.getCurrentPage();
    var total_emails = this.getEMailsCount()
    return {
        from: (page-1)*pageSize + 1,
        to: Math.min(page*pageSize, total_emails),
        total_emails: total_emails
    };
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

EMailsManager.prototype.removeEMails = function(ids, from_cache) {
    if (ids === undefined) {
        throw("EMailsManager: Undefined ids.");
    }
    if (from_cache === undefined) from_cache = false;

    for(var i = 0; i < ids.length; i++) {
        this.source.remove(ids[i]);
        if (from_cache) {
            delete this.cache[this.toCacheId(ids[i])];
        }
    }
}

EMailsManager.prototype.loadEMails = function(page) {
    if (!this.requestInProgress) { 
        this.requestInProgress = true;
        if (this.callbacks.onLoad !== undefined) {
            this.callbacks.onLoad();
        }

        var pageSize = this.getPageSize();
        var page_ids = this.source.getIds().slice((page-1)*pageSize, 
                                                  page*pageSize);
        var new_ids = page_ids;

        if (this.caching) { // load only new e-mails when caching is on
            new_ids = [];
            for (var i = 0; i < page_ids.length; i++) {
                if (!(this.toCacheId(page_ids[i]) in this.cache)) {
                    new_ids.push(page_ids[i]);
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
                            if (self.caching) {
                                for (var i = 0; i < page_ids.length; i++) {
                                    if (new_ids.indexOf(page_ids[i]) < 0) {
                                        response.data.push(
                                                self.cache[self.toCacheId(page_ids[i])]
                                            );
                                    }
                                }
                            }
                        }

                        console.log("response.ids: ", JSON.stringify(response.data));

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
                for (var i = 0; i < page_ids.length; i++) {
                    response.data.push(this.cache[this.toCacheId(page_ids[i])]);
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

EMailsManager.prototype.getIds = function() {
    if (this.source === undefined) {
        return undefined;
    }
    return (this.source.getIds());
};

EMailsManager.prototype.getEMailsCount = function() {
    if (this.source === undefined) {
        return undefined;
    }
    return (this.source.getEMailsCount());
};


/******************************************************************************
 * AbstractSource
 * - get emails ids from select
 ******************************************************************************/

function AbstractSource() {
    this.ids = undefined;
}

AbstractSource.prototype.update = function(callback) {
    throw("Not implmeneted.");
}

AbstractSource.prototype.remove = function(id) {
    if (this.ids !== undefined) {
        var index = this.ids.indexOf(id);
        if (index > -1) {
            this.ids.splice(index, 1);
            return (true);
        }
    }
    return (false);
}

AbstractSource.prototype.getIds = function() {
    return (this.ids);
}

AbstractSource.prototype.getEMailsCount = function() {
    if (this.ids === undefined) {
        return 0;
    } else {
        return this.ids.length;
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
SelectSource.prototype = Object.create(AbstractSource.prototype);
SelectSource.prototype.constructor = SelectSource;

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
SearchSource.prototype = Object.create(AbstractSource.prototype);
SearchSource.prototype.constructor = SearchSource;

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