#!/bin/bash

function static_mapping {
    echo "static_mapping"
    echo "=============="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./StaticMapping.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./StaticMapping.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./StaticMapping.apk 2> /dev/null
    echo ""
}

function static_mapping_overload {
    echo "static_mapping_overload"
    echo "======================="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./StaticMappingOverload.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./StaticMappingOverload.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./StaticMappingOverload.apk 2> /dev/null
    echo ""
}

function dynamic_mapping {
    echo "dynamic_mapping"
    echo "==============="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./DynamicMapping.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./DynamicMapping.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./DynamicMapping.apk 2> /dev/null
    echo ""
}

function dynamic_mapping_complex {
    echo "dynamic_mapping_complex"
    echo "======================="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./DynamicMappingComplex.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./DynamicMappingComplex.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./DynamicMappingComplex.apk 2> /dev/null
    echo ""
}

function dynamic_mapping_clash {
    echo "dynamic_mapping_clash"
    echo "====================="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./DynamicMappingClash.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./DynamicMappingClash.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./DynamicMappingClash.apk 2> /dev/null
    echo ""
}

function dynamic_mapping_nonglobal {
    echo "dynamic_mapping_nonglobal"
    echo "========================="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./DynamicMappingNonglobal.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./DynamicMappingNonglobal.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./DynamicMappingNonglobal.apk 2> /dev/null
    echo ""
}

function nested_lib {
    echo "nested_lib"
    echo "=========="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnested.so@target_fun ./NestedLib.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnested.so@target_fun ./NestedLib.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnested.so@target_fun ./NestedLib.apk 2> /dev/null
    echo ""
}

function indirect_jmp {
    echo "indirect_jmp"
    echo "============"
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./IndirectJmp.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./IndirectJmp.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./IndirectJmp.apk 2> /dev/null
    echo ""
}

function indirect_jmp_variant {
    echo "indirect_jmp_variant"
    echo "===================="
    echo "Using Androguard:"
    dreach --angr-bb-iterations 2 --reachable --find-path-to libnative.so@target_fun ./IndirectJmpVariant.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --angr-bb-iterations 2 --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./IndirectJmpVariant.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --angr-bb-iterations 2 --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./IndirectJmpVariant.apk 2> /dev/null
    echo ""
}

function indirect_jmp_variant2 {
    echo "indirect_jmp_variant2"
    echo "====================="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./IndirectJmpVariant2.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./IndirectJmpVariant2.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./IndirectJmpVariant2.apk 2> /dev/null
    echo ""
}

function high_depth {
    echo "high_depth"
    echo "=========="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./HighDepth.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./HighDepth.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./HighDepth.apk 2> /dev/null
    echo ""
}

function indirect_jmp_high_depth {
    echo "indirect_jmp_high_depth"
    echo "======================="
    echo "Using Androguard:"
    dreach --reachable --find-path-to libnative.so@target_fun ./IndirectJmpHighDepth.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./IndirectJmpHighDepth.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./IndirectJmpHighDepth.apk 2> /dev/null
    echo ""
}

function indirect_jmp_high_depth_variant {
    echo "indirect_jmp_high_depth_variant"
    echo "==============================="
    echo "Using Androguard:"
    dreach --angr-max-calldepth 10 --reachable --find-path-to libnative.so@target_fun ./IndirectJmpHighDepthVariant.apk 2> /dev/null
    echo ""
    echo "Full iCFG Path:"
    dreach --angr-max-calldepth 10 --print-full-icfg-path --reachable --find-path-to libnative.so@target_fun ./IndirectJmpHighDepthVariant.apk 2> /dev/null
    echo ""
    echo "Using FlowDroid:"
    dreach --angr-max-calldepth 10 --use-flowdroid --reachable --find-path-to libnative.so@target_fun ./IndirectJmpHighDepthVariant.apk 2> /dev/null
    echo ""
}

if [ "$1" != "" ]; then
    $1
    exit 0
fi

static_mapping
static_mapping_overload
dynamic_mapping
dynamic_mapping_clash
dynamic_mapping_nonglobal
nested_lib
indirect_jmp
indirect_jmp_variant
indirect_jmp_variant2
high_depth
indirect_jmp_high_depth
indirect_jmp_high_depth_variant
