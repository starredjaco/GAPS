#include <android/log.h>
#include <jni.h>
#include <string>

#define LOG_TAG    "trigger"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void target_fun() {
    LOGI("call: target_fun()");
}

void trigger() {
    target_fun();
}

static const JNINativeMethod methods[] = {
        {"trigger", "()V", reinterpret_cast<void*>(trigger)},
};

JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    jclass c = env->FindClass("liana/app/dynamicmapping/MainActivity");
    if (c == nullptr) return JNI_ERR;

    int rc = env->RegisterNatives(c, methods, 1);
    if (rc != JNI_OK) return rc;

    return JNI_VERSION_1_6;
}
