Java.perform(function() {
    var class_hook = Java.use('android.content.Intent');

    class_hook.$init.overload().implementation = function(){
        send('[Method] android.content.Intent.$init() reached');
        var retval = this.$init();
        return retval;
    };

});
