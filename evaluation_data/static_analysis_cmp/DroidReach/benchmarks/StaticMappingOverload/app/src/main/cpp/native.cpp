#include <android/log.h>
#include <jni.h>
#include <string>

#define LOG_TAG    "trigger"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void target_fun(int v)
{
    LOGI("call: target_fun(%d)", v);
}

extern "C"
JNIEXPORT void JNICALL
Java_liana_app_staticmappingoverload_MainActivity_trigger__I(JNIEnv *env, jobject thiz, jint a) {
    target_fun(a);
}

extern "C"
JNIEXPORT void JNICALL
Java_liana_app_staticmappingoverload_MainActivity_trigger__J(JNIEnv *env, jobject thiz, jlong a) {
}
