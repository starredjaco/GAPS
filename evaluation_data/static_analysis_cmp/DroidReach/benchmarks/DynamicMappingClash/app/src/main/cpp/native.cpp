#include <android/log.h>
#include <jni.h>
#include <string>

#define LOG_TAG    "trigger"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void target_fun() {
    LOGI("call: target_fun()");
}

void trigger_NativeClass2() {
    target_fun();
}

void trigger_NativeClass1() {
}

static const JNINativeMethod methods_NativeClass1[] = {
        {"trigger", "()V", reinterpret_cast<void*>(trigger_NativeClass1)},
};

static const JNINativeMethod methods_NativeClass2[] = {
        {"trigger", "()V", reinterpret_cast<void*>(trigger_NativeClass2)},
};

JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    jclass c;
    int rc;

    c = env->FindClass("liana/app/dynamicmappingclash/NativeClass1");
    if (c == nullptr) return JNI_ERR;

    rc = env->RegisterNatives(c, methods_NativeClass1, 1);
    if (rc != JNI_OK) return rc;

    c = env->FindClass("liana/app/dynamicmappingclash/NativeClass2");
    if (c == nullptr) return JNI_ERR;

    rc = env->RegisterNatives(c, methods_NativeClass2, 1);
    if (rc != JNI_OK) return rc;

    return JNI_VERSION_1_6;
}
