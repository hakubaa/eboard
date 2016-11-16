function isPartOf(task, spec) {
    if (task === spec) return true;
    if (!(task instanceof Object) || !(spec instanceof Object)) return false;

    if (task.constructor === Array) {
        if (spec.constructor === Array) {
            var specFound = 0;
            for (var i = 0; i < spec.length; i++) {
                if (isPartOf(task, spec[i])) specFound += 1;
            }
            if (specFound != spec.length) return false;
        } else {
            var specFound = false;
            for(var i = 0; i < task.length; i++) {  
                if (isPartOf(task[i], spec)) {
                    specFound = true;
                    break;
                }
            }
            if (!specFound) return false;
        }
    } else {
        if (spec.constructor === Array) return false;
        var specKeys = Object.keys(spec);   
        for (var i = 0; i < specKeys.length; i++) {
            if (specKeys[i] in task) {
                if (!isPartOf(task[specKeys[i]], spec[specKeys[i]])) {
                    return false;
                }
            } else { // lack of one of spec's key in task
                return false;
            }
        }
    }
    return true;
}

function getPropByString(obj, propString) {
    if (!propString)
        return obj;

    var prop, props = propString.split('.');

    for (var i = 0, iLen = props.length - 1; i < iLen; i++) {
        prop = props[i];

        var candidate = obj[prop];
        if (candidate !== undefined) {
            obj = candidate;
        } else {
            break;
        }
    }
    return obj[props[i]];
}

function dynamicSort(property) {
    var sortOrder = 1;
    if(property[0] === "-") {
        sortOrder = -1;
        property = property.substr(1);
    }
    return function (a,b) {
        var aProp = getPropByString(a, property);
        var bProp = getPropByString(b, property);
        var result = (aProp < bProp) ? -1 : (aProp > bProp) ? 1 : 0;
        return result * sortOrder;
    }
}

function dynamicSortMultiple() {
    /*
     * save the arguments object as it will be overwritten
     * note that arguments object is an array-like object
     * consisting of the names of the properties to sort by
     */
    var props = arguments;
    return function (obj1, obj2) {
        var i = 0, result = 0, numberOfProperties = props.length;
        /* try getting a different result from 0 (equal)
         * as long as we have extra properties to compare
         */
        while(result === 0 && i < numberOfProperties) {
            result = dynamicSort(props[i])(obj1, obj2);
            i++;
        }
        return result;
    }
}