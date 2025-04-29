Java.perform(function() {
    var class_hook = Java.use('com.fly.web.smart.browser.ui.recommend.RecommendWebsitesActivity');

    class_hook.q.overload().implementation = function(){
        send('[Method] com.fly.web.smart.browser.ui.recommend.RecommendWebsitesActivity.q() reached');
        var retval = this.q();
        return retval;
    };

});
