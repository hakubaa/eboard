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

    this.emailsPerPage = Math.ceil(options.emailsPerPage);
    this.requestInProgress = false;
    this.callbacks = {
        onLoad: undefined,
        onLoaded: undefined
    };
}

EMailsManager.prototype.init = function(options) {
    this.mailbox = options.mailbox;
    this.page = 1;
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
}

EMailsManager.prototype.prevPage = function() {
    if (this.hasPrevPage()) {
        this.loadEMails(this.getCurrentPage() - 1);
    }
}

EMailsManager.prototype.loadEMails = function(page) {
    if (!this.requestInProgress) { 
        this.requestInProgress = true;
        
        if (this.callbacks.onLoad !== undefined) {
            this.callbacks.onLoad();
        }

        var self = this;

        var params;
        params = this.getIds(page);
        params.mailbox = this.getCurrentMailbox();
        params.callback = function(response) {
            if (response.status == "OK") {
                self.page = page;
            }
            if (self.callbacks.onLoaded !== undefined) {
                self.callbacks.onLoaded(response);
            }
            self.requestInProgress = false;
        };
        getEMailsHeaders(params);      
    } else {
        alert("E-mails are being loaded. Please wait a second with " +
              "your next request.");
    }     
};

/******************************************************************************
 * SelectManager
 * - iterate all emails in selected mailbox
 ******************************************************************************/

function SelectManager(options) {
    if (options === undefined) options = {};
    EMailsManager.call(this, options);
    this.total_emails = undefined;
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
    getEMailsCount({
        mailbox: options.mailbox,
        callback: function(response) {
            if (response.status === "OK") {
                self.total_emails = response.data;
            }
            if (options.callback !== undefined) {
                options.callback(response);
            }
        }
    });
};

SelectManager.prototype.hasNextPage = function() {
    if (this.total_emails === undefined || this.total_emails === 0) {
        return false;
    }

    var page = this.getCurrentPage();
    var pageSize = this.getPageSize();
    if (this.total_emails - page*pageSize > 0) {
        return true;
    } 
    return false;
};

SelectManager.prototype.hasPrevPage = function() {
    var page = this.getCurrentPage();
    if (this.total_emails === undefined || this.total_emails === 0 || page === 1) {
        return false;
    }
    return true;
};

SelectManager.prototype.getIds = function(page) {
    if (this.total_emails === undefined) {
        return undefined;
    }
    return {
        from: this.calcFrom(page),
        to: this.calcTo(page)    
    };    
};

SelectManager.prototype.calcFrom = function(page) {
    if (page === undefined || page === null || page == 0) {
        return 1;
    }
    var pageSize = this.getPageSize();
    var emailsFrom = 1 + (page - 1)*pageSize;
    if (this.total_emails !== undefined)
        emailsFrom = Math.min(emailsFrom, this.total_emails)
    return emailsFrom;
};

SelectManager.prototype.calcTo = function(page) {
    var pageSize = this.getPageSize();
    if (page === undefined || page === null || page == 0) {
        return Math.min(pageSize, this.total_emails);
    } 
    var emailsTo = page * pageSize;
    if (this.total_emails !== undefined)
        emailsTo = Math.min(emailsTo, this.total_emails)     
    return emailsTo;
};

SelectManager.prototype.getEMailsCount = function() {
    if (this.total_emails === undefined) {
        return 0;
    } else {
        return this.total_emails;
    }
}

/******************************************************************************
 * SearchManager 
 * - iterate emails returns by search method
 ******************************************************************************/

function SearchManager(options) {
    if (options === undefined) options = {};
    EMailsManager.call(this, options);
    this.ids = undefined;
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
            callback: function(response) {
                if (response.status === "OK") {
                    self.ids = response.data;
                }
                if (options.callback !== undefined) {
                    options.callback(response);
                }         
            }
        });
};

SearchManager.prototype.hasNextPage = function() {
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

SearchManager.prototype.hasPrevPage = function() {
    var page = this.getCurrentPage();
    if (this.ids === undefined || this.ids.length === 0 || page === 1) {
        return false;
    }
    return true;
};

SearchManager.prototype.getIds = function(page) {
    if (this.ids === undefined) {
        return undefined;
    }
    var pageSize = this.getPageSize();
    return {
        ids: this.ids.slice((page-1)*pageSize, page*pageSize).join(",")  
    };
};

SearchManager.prototype.getEMailsCount = function() {
    if (this.ids === undefined) {
        return 0;
    } else {
        return this.ids.length;
    }
};