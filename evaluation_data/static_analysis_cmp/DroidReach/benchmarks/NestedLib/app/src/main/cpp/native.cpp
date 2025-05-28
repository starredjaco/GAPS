#include <jni.h>
#include <string>

void target_fun();

extern "C"
JNIEXPORT void JNICALL
Java_liana_app_nestedlib_MainActivity_trigger(JNIEnv *env, jobject thiz) {
    target_fun();
}
