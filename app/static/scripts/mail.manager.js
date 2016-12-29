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
    if (options.uid === undefined) {
        this.uid = false;
    } else {
        this.uid = options.uid;
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
        onLoaded: undefined
    };
    this.uid = options.uid;
    this.ids = undefined;
    this.cache = {};
}

EMailsManager.prototype.init = function(options) {
    if (options === undefined) options = {};
    this.mailbox = options.mailbox;
    this.page = 0;
}

EMailsManager.prototype.getCurrentPage = function() {
    return this.page;
}

EMailsManager.prototype.getPageSize = function() {
    return this.emailsPerPage;
}

EMailsManager.prototype.getCurrentMailbox = function() {
    return this.mailbox;
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
                ids: this.getIds(page).join(","),
                mailbox: this.getCurrentMailbox(),
                uid: this.uid,
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
                            for (var i = 0; i < ids.length; i++) {
                                if (!(ids[i] in new_ids)) {
                                    response.data.push(
                                            self.cache[self.toCacheId(ids[i])]
                                        );
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
                    response.push(this.cache[this.toCacheId(ids[i])]);
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
    if (this.ids === undefined || this.ids.length === 0) {
        return false;
    }

    var page = this.getCurrentPage();
    var pageSize = this.getPageSize();
    if (this.ids.length - page*pageSize > 0) {
        return true;
    } 
    return false;
};

EMailsManager.prototype.hasPrevPage = function() {
    var page = this.getCurrentPage();
    if (this.ids === undefined || this.ids.length === 0 || page < 2) {
        return false;
    }
    return true;
};

EMailsManager.prototype.getIds = function(page) {
    if (this.ids === undefined) {
        return undefined;
    }
    var pageSize = this.getPageSize();
    return (this.ids.slice((page-1)*pageSize, page*pageSize));
};

EMailsManager.prototype.getEMailsCount = function() {
    if (this.ids === undefined) {
        return 0;
    } else {
        return this.ids.length;
    }
};

/******************************************************************************
 * SelectManager
 * - iterate all emails in selected mailbox
 ******************************************************************************/

function SelectManager(options) {
    EMailsManager.call(this, options);
    
}
SelectManager.prototype = Object.create(EMailsManager.prototype);
SelectManager.prototype.constructor = SelectManager;

SelectManager.prototype.init = function(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw("SelectManager: undefined mailbox in init"); 
    }
    EMailsManager.prototype.init.call(this, options);

    var self = this;
    getEMailsList({
        mailbox: options.mailbox,
        uid: this.uid,
        callback: function(response) {
            if (response.status === "OK") {
                self.ids = response.data;
                self.ids.reverse();
            }
            if (options.callback !== undefined) {
                options.callback(response);
            }
        }
    });
};

/******************************************************************************
 * SearchManager 
 * - iterate emails returns by search method
 ******************************************************************************/

function SearchManager(options) {
    EMailsManager.call(this, options);
}
SearchManager.prototype = Object.create(EMailsManager.prototype);
SearchManager.prototype.constructor = SelectManager;

SearchManager.prototype.init = function(options) {
    if (options === undefined) options = {};
    if (options.mailbox === undefined) {
        throw("SearchManager: undefined mailbox in init"); 
    }
    if (options.criteria === undefined) {
        throw("SearchManager: undefined criteria in init"); 
    }
    EMailsManager.prototype.init.call(this, options);

    var self = this;
    searchEMails({
            mailbox: options.mailbox,
            criteria: options.criteria,
            uid: this.uid,
            callback: function(response) {
                if (response.status === "OK") {
                    self.ids = response.data;
                    self.ids.reverse();
                }
                if (options.callback !== undefined) {
                    options.callback(response);
                }         
            }
        });
};