import os
import sys
import hashlib
import time
import json
import logging
import claripy
import subprocess
import networkx as nx

from shutil import copyfile
from collections import namedtuple
from androguard.session import Session
from androguard.misc import AnalyzeAPK

from networkx.classes.reportviews import NodeView

SCRIPTPATH = os.path.dirname(os.path.abspath(__file__))

NativeMethod = namedtuple(
    "NativeMethod",
    ["class_name", "method_name", "args_str", "libpath", "libhash", "offset"],
)

LOADLIB_TARGET = "Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V"


class APKAnalyzerError(Exception):
    pass


def reformat_comp(raw_comp: str):
    """
    Format dot-separated class names into slash-separated ones
    :param raw_comp:
    :return:
    """
    return raw_comp.replace(".", "/")


def find_nodes_from_class(cl: str, nodes: NodeView):
    """
    get nodes in the graph associated with input class
    :param cl:
    :param nodes:
    :return:
    """
    return [str(n) for n in nodes if cl in n.split(";->")[0]]


class AppComponent:
    """
    Small convenience class for some component's attributes and methods
    """

    def __init__(self, name, vals, exported_components):
        self.name = name
        self.vals = [reformat_comp(v) for v in vals]
        for val in self.vals:
            if val not in exported_components:
                self.vals.remove(val)

    def get_sources(self, graph_nodes: NodeView):
        """
        Get nodes associated with the components. These will represent the starting points within paths

        :param graph_nodes:
        :return:
        """
        tmp = [find_nodes_from_class(v, graph_nodes) for v in self.vals]
        return list(set([item for sublist in tmp for item in sublist]))


class FileNotFoundException(APKAnalyzerError):
    def __init__(self, fname):
        self.message = "%s not found" % fname
        super().__init__(self.message)


def md5_hash(f):
    with open(f, "rb") as f_binary:
        md5 = hashlib.md5(f_binary.read()).hexdigest()
    return md5


def connected_nodes(G, sources=list, depth_limit=None):
    nodes = list(sources)
    visited = set()
    if depth_limit is None:
        depth_limit = len(G)
    for start in nodes:
        if start in visited:
            continue
        yield start
        visited.add(start)
        stack = [(start, depth_limit, iter(G[start]))]
        while stack:
            parent, depth_now, children = stack[-1]
            try:
                child = next(children)
                if child not in visited:
                    yield child
                    visited.add(child)
                    if depth_now > 1:
                        stack.append((child, depth_now - 1, iter(G[child])))
            except StopIteration:
                stack.pop()


def get_static_constructors_map(nodes: NodeView):
    res = dict()
    for node in nodes:
        node_str = str(node)
        class_name = node_str.split("->")[0]
        method_name = node_str.split("->")[1].split("(")[0]
        if method_name == "<clinit>":
            res[class_name] = node_str
    return res


class APKAnalyzer(object):
    # FIXME: a refactoring is required
    #        probably we can use JNIFunctionDescription (defined by NativeLibAnalyzer) only locally
    #        and always return NativeMethod instances. Furthermore, we HAVE to get rid of 'analyzer'
    #        ptrs and only use the API get_native_analyzer

    log = logging.getLogger("ap.APKAnalyzer")
    log.setLevel(logging.DEBUG)
    # from androguard.util import set_log

    # set_log("ERROR")

    tmp_dir = "../results"

    def _create_dirs(self):
        if not os.path.exists(APKAnalyzer.tmp_dir):
            os.mkdir(APKAnalyzer.tmp_dir)
        if not os.path.exists(self.wdir):
            os.mkdir(self.wdir)

        if not os.path.exists(
            os.path.join(self.wdir, os.path.basename(self.apk_path))
        ):
            copyfile(
                self.apk_path,
                os.path.join(self.wdir, os.path.basename(self.apk_path)),
            )

    def __init__(self, apk_path, use_flowdroid=False):
        if not os.path.exists(apk_path):
            APKAnalyzer.log.error(f"{apk_path} does not exist")
            raise FileNotFoundException(apk_path)

        APKAnalyzer.log.info("APKAnalyzer initialization")
        self.use_flowdroid = use_flowdroid
        self.apk_path = apk_path
        self.apk_name = os.path.basename(self.apk_path).replace(".apk", "")
        self.apk_hash = md5_hash(self.apk_path)
        self.wdir = os.path.join(APKAnalyzer.tmp_dir, self.apk_name)
        self.apk, self.dvm, self.analysis = None, None, None
        self.androguard_session = None

        self.callgraph_flowdroid_filename = os.path.join(
            self.wdir, "callgraph_flowdroid.json"
        )
        self.callgraph_androguard_filename = os.path.join(
            self.wdir, "callgraph_androguard.gml"
        )
        self.pruned_callgraph_filename = os.path.join(
            self.wdir, "pruned_callgraph_androguard.gml"
        )
        self.cfgs_json_filename = os.path.join(self.wdir, "cfgs.json")
        self.callgraph_flowdroid = None
        self.callgraph_androguard = None
        self.paths_json_filename = (
            os.path.join(self.wdir, "androguard_paths_fe.json")
            if not use_flowdroid
            else os.path.join(self.wdir, "flowdroid_paths.json")
        )
        self.cfgs = None
        self.paths = None
        self.lib_dep_graph = None
        self._create_dirs()

        self.package_name = None
        self._native_libs = None
        self._native_lib_analysis = None
        self._native_methods = None
        self._native_methods_reachable = None

        APKAnalyzer.log.info("APKAnalyzer initialization done")

    def _lazy_apk_init(self):
        if self.apk is not None:
            return
        self.androguard_session = Session()
        self.apk, self.dvm, self.analysis = AnalyzeAPK(
            self.apk_path, session=self.androguard_session
        )
        self.package_name = self.apk.get_package()

    def _get_exported_components(self):
        exported_components = set()
        component_types = ["activity", "service", "receiver", "provider"]
        manifest_xml = self.apk.get_android_manifest_xml()
        package_name = manifest_xml.get("package").replace(".", "/")
        for component_type in component_types:
            components = manifest_xml.findall(
                f"./application/{component_type}"
            )
            if not components:
                continue
            for component in components:
                component_name_full = component.get(
                    "{http://schemas.android.com/apk/res/android}name"
                ).replace(".", "/")
                if package_name not in component_name_full:
                    component_name_full = package_name + component_name_full
                permission = component.get(
                    "{http://schemas.android.com/apk/res/android}permission"
                )
                if (
                    component.get(
                        "{http://schemas.android.com/apk/res/android}exported"
                    )
                    == "true"
                    and not permission
                ):
                    exported_components.add(component_name_full)
            java_name = component_name_full.replace("/", ".")
            for action, intent_name in self.apk.get_intent_filters(
                component_type, java_name
            ).items():
                if action == "action":
                    exported_components.add(component_name_full)
        return exported_components

    def get_cfgs(self):
        if self.cfgs is not None:
            return self.cfgs

        cfgs_json = None
        if not os.path.exists(self.cfgs_json_filename):
            self._lazy_apk_init()
            res = {"classes": dict()}
            for _, vm, vmx in self.androguard_session.get_objects_dex():
                for method in vm.get_methods():
                    class_name = str(method.get_class_name())
                    if class_name not in res["classes"]:
                        res["classes"][class_name] = {"methods": list()}
                    class_json = res["classes"][class_name]

                    method_name = str(method.get_name())
                    method_descriptor = str(method.get_descriptor())
                    method_json = {
                        "name": method_name,
                        "descriptor": method_descriptor,
                        "basic_blocks": list(),
                    }
                    class_json["methods"].append(method_json)

                    am = vmx.get_method(method)
                    bbs = am.get_basic_blocks()
                    for bb in bbs.bb:
                        bb_json = {
                            "start": bb.start,
                            "instructions": list(),
                            "successors": [x[1] for x in bb.get_next()],
                        }
                        method_json["basic_blocks"].append(bb_json)

                        idx = bb.start
                        for insn in bb.get_instructions():
                            bb_json["instructions"].append(
                                {
                                    "idx": idx,
                                    "mnemonic": "%s %s"
                                    % (insn.get_name(), insn.get_output(0)),
                                }
                            )
                            idx += insn.get_length()
            with open(self.cfgs_json_filename, "w") as fout:
                fout.write(json.dumps(res))
            cfgs_json = res

        if cfgs_json is None:
            with open(self.cfgs_json_filename, "r") as fin:
                cfgs_json = json.load(fin)

        self.cfgs = dict()
        for c in cfgs_json["classes"]:
            for m in cfgs_json["classes"][c]["methods"]:
                method_id = "%s->%s%s" % (c, m["name"], m["descriptor"])
                self.cfgs[method_id] = nx.DiGraph()
                cfg = self.cfgs[method_id]
                for bb in m["basic_blocks"]:
                    label = ""
                    if bb["start"] == 0:
                        label += "%s\n\n" % method_id
                    label += "\n".join(
                        [
                            "%02d: %s" % (x["idx"], x["mnemonic"])
                            for x in bb["instructions"]
                        ]
                    )
                    cfg.add_node(
                        bb["start"],
                        ids=[x["idx"] for x in bb["instructions"]],
                        label=label,
                    )
                for bb in m["basic_blocks"]:
                    for s in bb["successors"]:
                        cfg.add_edge(bb["start"], s)
        return self.cfgs

    def get_callgraph_flowdroid(self):
        # Todo: add callsites
        flowdroid_bin = os.path.join(SCRIPTPATH, "bin/FlowdroidCGDumper.jar")
        platforms_dir = os.path.join(
            os.path.expanduser("~"), "Android/Sdk/platforms"
        )
        if not os.path.exists(platforms_dir):
            platforms_dir = "/opt/android-sdk/platforms"
            if not os.path.exists(platforms_dir):
                APKAnalyzer.log.error(
                    "unable to find android sdk for building the callgraph with flowdroid"
                )
                return None

        APKAnalyzer.log.info("generating Flowdroid callgraph")
        fout = open(self.callgraph_flowdroid_filename, "w")
        cg = subprocess.run(
            [
                "java",
                "-jar",
                flowdroid_bin,
                platforms_dir,
                self.apk_path,
            ],
            stdout=fout,
            # stderr=subprocess.DEVNULL,
        )
        fout.close()
        APKAnalyzer.log.info(
            f"callgraph generated in {self.callgraph_flowdroid_filename}"
        )

        with open(self.callgraph_flowdroid_filename, "r") as fin:
            cg = json.load(fin)

        APKAnalyzer.log.info("reading callgraph")
        self.callgraph_flowdroid = nx.MultiDiGraph()
        for edge in cg["edges"]:
            src = "L" + edge["src"][1:-1].replace(": ", ";->").replace(
                ".", "/"
            )
            dst = "L" + edge["dst"][1:-1].replace(": ", ";->").replace(
                ".", "/"
            )
            self.callgraph_flowdroid.add_edge(src, dst)
        APKAnalyzer.log.info("callgraph read")

        sources = list()
        for node in self.callgraph_flowdroid:
            if str(node).startswith("LdummyMainClass;->dummyMainMethod_"):
                sources.append(str(node))

        return self.callgraph_flowdroid, sources

    def get_callgraph_androguard(self):
        APKAnalyzer.log.info("generating androguard callgraph")
        cg = subprocess.run(
            [
                "androguard",
                "cg",
                "-o",
                self.callgraph_androguard_filename,
                self.apk_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        APKAnalyzer.log.info(
            f"callgraph generated in {self.callgraph_androguard_filename}"
        )

        APKAnalyzer.log.info("reading callgraph")
        self.callgraph_androguard = nx.read_gml(
            self.callgraph_androguard_filename
        )

        def relable_function(name):
            return name.split(" ")[1]

        self.callgraph_androguard = nx.relabel_nodes(
            self.callgraph_androguard, relable_function
        )
        APKAnalyzer.log.info("callgraph read")

        self._lazy_apk_init()
        self.exported_components = self._get_exported_components()
        acts = AppComponent(
            "a", self.apk.get_activities(), self.exported_components
        )
        provs = AppComponent(
            "p", self.apk.get_providers(), self.exported_components
        )
        recvs = AppComponent(
            "r", self.apk.get_receivers(), self.exported_components
        )
        servs = AppComponent(
            "s", self.apk.get_services(), self.exported_components
        )
        static_constructors = get_static_constructors_map(
            self.callgraph_androguard.nodes
        )

        components = [acts, provs, recvs, servs]
        sources = list()
        for comp in components:
            sources.extend(comp.get_sources(self.callgraph_androguard.nodes))

        n_sources = len(sources)
        connected_subgraph = self.callgraph_androguard.subgraph(
            connected_nodes(self.callgraph_androguard, sources)
        )

        # Add static constructors of classes that are used by the application
        added_class = set()
        for node in connected_subgraph.nodes:
            node_str = str(node)
            class_name = node_str.split("->")[0]
            if class_name in added_class:
                continue
            added_class.add(class_name)
            if class_name in static_constructors:
                sources.append(static_constructors[class_name])
        n_added_static_sources = len(sources) - n_sources
        APKAnalyzer.log.info(
            f"added {n_added_static_sources} static constructors as sources"
        )

        connected_subgraph = self.callgraph_androguard.subgraph(
            connected_nodes(self.callgraph_androguard, sources)
        )
        nx.readwrite.gml.write_gml(
            connected_subgraph, self.pruned_callgraph_filename
        )

        return self.callgraph_androguard, sources

    def get_callgraph(self):
        if not self.use_flowdroid:
            cg, _ = self.get_callgraph_androguard()
        else:
            cg, _ = self.get_callgraph_flowdroid()
        return cg

    def get_paths_to_java_methods(self, targets):

        APKAnalyzer.log.info("generating paths to native functions")

        self._lazy_apk_init()
        if not self.use_flowdroid:
            cg, sources = self.get_callgraph_androguard()
        else:
            cg, sources = self.get_callgraph_flowdroid()

        APKAnalyzer.log.info(
            f"looking for {len(targets)} targets and {len(sources)} sources"
        )
        print(f"sources #{len(sources)}")
        cg_reversed = cg.reverse()
        APKAnalyzer.log.info("looking for paths")
        paths = {}
        for t in targets:
            for s in sources:
                if s not in cg.nodes or t not in cg.nodes:
                    continue
                link = next(
                    nx.all_simple_paths(cg_reversed, source=t, target=s), None
                )
                if link is None:
                    continue
                if t not in paths:
                    paths[t] = list()
                paths[t].append(link[::-1])

        print(f"found {len(paths)} paths")

        self.paths = {"md5": self.apk_hash, "paths": paths}

        with open(self.paths_json_filename, "a+") as f_out:
            f_out.write(json.dumps(self.paths, indent=4))
        APKAnalyzer.log.info(f"paths dumped in {self.paths_json_filename}")
        return self.paths

    def get_path_to_native_method(self, method):
        paths_result = self.get_paths_to_native()
        for n in paths_result["paths"]:
            native_name = n.split(";->")[1].split("(")[0]
            class_name = n.split(";->")[0] + ";"
            if (
                class_name == method.class_name
                and native_name == method.method_name
            ):
                java_path = list()
                for j in paths_result["paths"][n]:
                    native_name = j.split(";->")[1].split("(")[0]
                    class_name = j.split(";->")[0] + ";"
                    args = "(" + j.split(";->")[1].split("(")[1]
                    java_path.append(class_name + "->" + native_name + args)
                return java_path
        return None
