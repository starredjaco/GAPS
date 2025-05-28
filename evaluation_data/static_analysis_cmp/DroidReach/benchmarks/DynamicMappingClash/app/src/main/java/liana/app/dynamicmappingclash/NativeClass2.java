package liana.app.dynamicmappingclash;

public class NativeClass2 {
    static {
        System.loadLibrary("native");
    }

    public native void trigger();
}
