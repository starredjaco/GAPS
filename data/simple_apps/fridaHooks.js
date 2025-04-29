Java.perform(function() {
    var class_hook = Java.use('com.simplemobiletools.clock.activities.ReminderActivity');

    class_hook.I.overload('java.lang.Integer').implementation = function(arg0){
        send('[Method] com.simplemobiletools.clock.activities.ReminderActivity.I(java.lang.Integer) reached');
        var retval = this.I(arg0);
        return retval;
    };

});
