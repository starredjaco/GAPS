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
        LOGI("call: foo()");
        target_fun();
    }
};

void e(Obj* o) {
    LOGI("call: e()");
    o->foo();
}

void d(Obj* o) {
    LOGI("call: d()");
    e(o);
}

void c(Obj* o) {
    LOGI("call: c()");
    d(o);
}

void b(Obj* o) {
    LOGI("call: b()");
    c(o);
}

void a(Obj* o) {
    LOGI("call: a()");
    b(o);
}

extern "C"
JNIEXPORT void JNICALL
Java_liana_app_indirectjmphighdeptvariant_MainActivity_trigger(JNIEnv *env, jobject thiz) {
    Obj* o = new Obj();
    a(o);

    delete o;
}