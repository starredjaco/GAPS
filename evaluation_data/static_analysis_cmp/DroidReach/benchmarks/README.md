# DroidReachBenchmarks

Benchmark apps that highlights reachability analysis challenges in the native world of Android applications.

The compiled applications are stored under the `apks` subdirectory.

### Benchmarks

|id  | name                        | description                                                                              | ArgusSaf    | Ghidra      | DroidReach  |
|----|-----------------------------|------------------------------------------------------------------------------------------|-------------|-------------|-------------|
| 0  | StaticMapping               | JNI Method bound to a Java native method through name mangling                           | &#9746;     | n/a         | &#9746;     |
| 1  | StaticMappingOverload       | JNI Method bound to a Java native method through name mangling (method overload)         | &#9746;     | n/a         | &#9746;     |
| 2  | DynamicMapping              | JNI Method bound to a Java native method using RegisterNatives API                       | &#9746; (1) | n/a         | &#9746;     |
| 3  | DynamicMappingClash         | JNI Method bound to a Java native method using RegisterNatives API (clash in class name) | &#9746; (1) | n/a         | &#9746; (1) |
| 4  | DynamicMappingNonglobal     | JNI Method bound to a Java native method using RegisterNatives API (non-global array)    | &#9746; (1) | n/a         | &#9746; (1) |
| 5  | DynamicMappingComplex       | JNI Method bound to a Java native method using RegisterNatives API (complex code)        | &#9744;     | n/a         | &#9746;     |
| 6  | NestedLib                   | JNI Method calls another linked library                                                  | &#9744; (2) | &#9744; (3) | &#9746;     |
| 7  | HighDepth                   | The target function is called with a high calldepth                                     | &#9744; (4) | &#9746;     | &#9746;     |
| 8  | IndirectJmp                 | The target function is called after an indirect call (C++ virtual call)                   | &#9746;     | &#9744;     | &#9746;     |
| 9  | IndirectJmpVariant          | The target function is called after an indirect call (C++ virtual call)                   | &#9746;     | &#9744;     | &#9746;     |
| 10 | IndirectJmpVariant2         | The target function is called after an indirect call (function pointer)                   | &#9746;     | &#9744;     | &#9746;     |
| 11 | IndirectJmpHighDepth        | The target function is called at a high calldepth after an indirect call (at small depth)   | &#9744; (4) | &#9744;     | &#9746;     |
| 12 | IndirectJmpHighDepthVariant | The target function is called at a high calldepth after an indirect call (at high depth)    | &#9744; (4) | &#9744;     | &#9744; (4) |

(1): Slow, uses symbolic execution.

(2): For the coarse-grained evaluation, we developed a variant of ArgusSaf that can reason on nested libraries

(3): For the coarse-grained evaluation, Ghidra was enhanced to deal with nested libraries

(4): It is possible to increase the calldepth, but there is a trade-off between running time/memory usage and desired calldepth.

n/a: not applicable, e.g., Ghidra is not involved in the resolution of JNI mapping. 
