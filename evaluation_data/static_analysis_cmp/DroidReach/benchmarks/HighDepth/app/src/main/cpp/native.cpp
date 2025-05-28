#include <android/log.h>
#include <jni.h>
#include <string>

#define LOG_TAG    "trigger"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void target_fun() {
    LOGI("call: target_fun()");
}

void e() {
    target_fun();
}

void d() {
    e();
}

void c() {
    d();
}

void b() {
    c();
}

void a() {
    b();
}

extern "C"
JNIEXPORT void JNICALL
Java_liana_app_highdepth_MainActivity_trigger(JNIEnv *env, jobject thiz) {
    a();
}
