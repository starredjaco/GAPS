#include <android/log.h>
#include <jni.h>
#include <string>

#define LOG_TAG    "trigger"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void target_fun() {
    LOGI("call: target_fun()");
}

class Obj {
public:
    virtual void foo() {
        target_fun();
    }
};

extern "C"
JNIEXPORT void JNICALL
Java_liana_app_indirectjmp_MainActivity_trigger(JNIEnv *env, jobject thiz) {
    Obj* o = new Obj();
    o->foo();

    delete o;
}