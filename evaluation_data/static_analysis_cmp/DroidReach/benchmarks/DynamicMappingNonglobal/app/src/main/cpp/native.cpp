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

JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    jclass c = env->FindClass("liana/app/dynamicmappingnonglobal/MainActivity");
    if (c == nullptr) return JNI_ERR;

    char name[] = "trigger\0";
    char signature[] = "()V\0";
    void* fnPtr = reinterpret_cast<void*>(trigger);
    JNINativeMethod mtd = {
            .name = name,
            .signature = signature,
            .fnPtr = fnPtr
    };
    JNINativeMethod methods[] = {mtd};

    int rc = env->RegisterNatives(c, methods, 1);
    if (rc != JNI_OK) return rc;

    return JNI_VERSION_1_6;
}
