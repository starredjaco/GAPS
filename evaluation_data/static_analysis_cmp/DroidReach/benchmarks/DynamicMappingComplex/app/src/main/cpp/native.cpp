#include <android/log.h>
#include <jni.h>
#include <vector>
#include <string>

#define LOG_TAG    "trigger"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void target_fun() {
    LOGI("call: target_fun()");
}

void trigger1() {
    LOGI("call: trigger1()");
}

void trigger2() {
    LOGI("call: trigger2()");
}

void trigger3() {
    LOGI("call: trigger3()");
    target_fun();
}

static const JNINativeMethod methods[] = {
        {"trigger1", "()V", reinterpret_cast<void*>(trigger1)},
        {"trigger2", "()V", reinterpret_cast<void*>(trigger2)},
        {"trigger3", "()V", reinterpret_cast<void*>(trigger3)},
};

JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    jclass c = env->FindClass("liana/app/dynamicmappingcomplex/MainActivity");
    if (c == nullptr) return JNI_ERR;

    std::vector<JNINativeMethod> vec;
    vec.push_back(methods[0]);
    vec.push_back(methods[1]);
    vec.push_back(methods[2]);

    int rc = env->RegisterNatives(c, vec.data(), vec.size());
    if (rc != JNI_OK) return rc;

    return JNI_VERSION_1_6;
}
