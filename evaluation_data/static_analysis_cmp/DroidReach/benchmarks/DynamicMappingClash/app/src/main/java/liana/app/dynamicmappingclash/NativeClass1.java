package liana.app.dynamicmappingclash;

public class NativeClass1 {
    static {
        System.loadLibrary("native");
    }

    public native void trigger();
}
