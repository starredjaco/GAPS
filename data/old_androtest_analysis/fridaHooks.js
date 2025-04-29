Java.perform(function() {
    var class_hook = Java.use('com.teleca.jamendo.activity.PlayerActivity');

    class_hook.$init.overload().implementation = function(){
        send('[Method] com.teleca.jamendo.activity.PlayerActivity.$init() reached');
        var retval = this.$init();
        return retval;
    };

});
