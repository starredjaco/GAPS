from androguard.core import apk, dex
from androguard.core.analysis.analysis import (
    Analysis,
)
from enum import IntEnum
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import dalvik_disassembler
from . import method_utils

from loguru import logger
import os

logger.remove()


class Operand(IntEnum):
    """
    Enumeration used for the operand type of opcodes
    """

    REGISTER = 0
    LITERAL = 1
    RAW = 2
    OFFSET = 3
    KIND = 0x100


class Kind(IntEnum):
    """
    This Enum is used to determine the kind of argument
    inside an Dalvik instruction.

    It is used to reference the actual item instead of the refernece index
    from the :class:`ClassManager` when disassembling the bytecode.
    """

    # Indicates a method reference
    METH = 0
    # Indicates that opcode argument is a string index
    STRING = 1
    # Indicates a field reference
    FIELD = 2
    # Indicates a type reference
    TYPE = 3
    # indicates a prototype reference
    PROTO = 9
    # indicates method reference and proto reference (invoke-polymorphic)
    METH_PROTO = 10
    # indicates call site item
    CALL_SITE = 11

    VARIES = 4
    # inline lined stuff
    INLINE_METHOD = 5
    # static linked stuff
    VTABLE_OFFSET = 6
    FIELD_OFFSET = 7
    RAW_STRING = 8


def AnalyzeAPK(_file, gaps, raw=False):
    """
    Analyze an android application and setup all stuff for a more quickly
    analysis!
    If session is None, no session is used at all. This is the default
    behaviour.
    If you like to continue your work later, it might be a good idea to use a
    session.
    A default session can be created by using :meth:`~get_default_session`.

    :param _file: the filename of the android application or a buffer which represents the application
    :type _file: string (for filename) or bytes (for raw)
    :param raw: boolean if raw bytes are supplied instead of a filename
    :rtype: return the :class:`~androguard.core.apk.APK`, list of :class:`~androguard.core.dvm.DEX`, and :class:`~androguard.core.analysis.analysis.Analysis` objects
    """
    a = apk.APK(_file, raw=raw)
    dx = myAnalysis()
    for dex_bytes in a.get_all_dex():
        df = dex.DEX(dex_bytes, using_api=a.get_target_sdk_version())
        dx.add(df)

    dx.create_xref(gaps, a)

    return a, dx


class myAnalysis(Analysis):
    def create_xref(self, gaps, a) -> None:
        """
        Create Method crossreferences
        for all classes in the Analysis.

        If you are using multiple DEX files, this function must
        be called when all DEX files are added.
        If you call the function after every DEX file, it will only work
        for the first time.
        """
        all_methods = [defaultdict(set), defaultdict(set)]

        starting_points_set = str(set(gaps.starting_points.keys()))
        analysis_blacklist = set()

        with dalvik_disassembler.ANDROLIBZOO.open() as f:
            for pkg in map(str.strip, f):
                if (
                    pkg not in starting_points_set
                    and pkg not in gaps.package_name
                ):
                    analysis_blacklist.add(pkg)

        max_workers = os.cpu_count() or 1
        with ThreadPoolExecutor(max_workers=max_workers) as e:

            futures = deque()

            for vm in self.vms:
                for current_class in vm.get_classes():
                    futures.append(
                        e.submit(
                            self._create_xref,
                            current_class,
                            all_methods,
                            analysis_blacklist,
                            gaps,
                        )
                    )

        for _ in as_completed(futures):
            pass

        dalvik_disassembler.save_testing_seeds(gaps, a, all_methods)

    def _create_xref(
        self, current_class, all_methods, analysis_blacklist, gaps
    ):
        """
        Create the xref for `current_class`

        There are four steps involved in getting the xrefs:
        * Xrefs for class instantiation and static class usage
        *       for method calls
        *       for string usage
        *       for field manipulation

        All these information are stored in the *Analysis Objects.

        Note that this might be quite slow, as all instructions are parsed.

        :param androguard.core.bytecodes.dvm.ClassDefItem current_class: The class to create xrefs for
        """
        class_name = str(current_class).split("->")[-1]
        if any(class_name.startswith(pkg) for pkg in analysis_blacklist):
            return
        for current_method in current_class.get_methods():
            method_obj = self.get_method(current_method)
            if method_obj.is_android_api():
                return None  # Skip API methods
            cur_meth = dalvik_disassembler._get_method_name(method_obj)
            class_name_parent, _ = method_utils.get_class_and_method(
                cur_meth, True
            )

            if ";->" in cur_meth:
                rest_signature_parent = cur_meth.split(";->", 1)[1].split()[0]
                gaps.all_methods[rest_signature_parent].add(cur_meth)

            for off, instruction in current_method.get_instructions_idx():
                if not any(
                    op in instruction.get_name()
                    for op in (
                        "invoke",
                        "put",
                        "get",
                        "check-cast",
                        "const-class",
                        "sparse-switch",
                        "packed-switch",
                        "return",
                    )
                ):
                    continue
                gaps.method_objs[gaps.method_index] = method_obj
                dalvik_disassembler.process_instr(
                    gaps,
                    instruction,
                    method_obj,
                    gaps.method_index,
                    cur_meth,
                    class_name_parent,
                    all_methods,
                )
                gaps.increment_method_index()
        return "finish"


def _get_operands(operands):
    """
    Return strings with color coded operands
    """
    for operand in operands:
        if operand[0] == Operand.REGISTER:
            yield "v{}".format(operand[1])

        elif operand[0] == Operand.LITERAL:
            yield "{}".format(operand[1])

        elif operand[0] == Operand.RAW:
            yield "{}".format(operand[1])

        elif operand[0] == Operand.OFFSET:
            yield "%d" % (operand[1])

        elif operand[0] & Operand.KIND:
            if operand[0] == (Operand.KIND + Kind.STRING):
                yield "{}".format(operand[2])
            elif operand[0] == (Operand.KIND + Kind.METH):
                yield "{}".format(operand[2])
            elif operand[0] == (Operand.KIND + Kind.FIELD):
                yield "{}".format(operand[2])
            elif operand[0] == (Operand.KIND + Kind.TYPE):
                yield "{}".format(operand[2])
            else:
                yield "{}".format(repr(operands[2]))
        else:
            yield "{}".format(repr(operands[1]))


def get_whole_method(basic_blocks):
    """
    Extract the whole method body from basic blocks.

    Args:
        basic_blocks: List of basic blocks.

    Returns:
        list: List of strings representing the method body.
    """
    idx = 0
    body = deque()
    for nb, i in enumerate(basic_blocks):
        header = "label: {}".format(i.get_name())
        body.append(header)
        instructions = list(i.get_instructions())
        for ins in instructions:
            content = ""
            content += "%s" % (ins.get_name())

            operands = ins.get_operands()
            content += " %s" % ", ".join(_get_operands(operands))

            op_value = ins.get_op_value()
            if ins == instructions[-1] and i.childs:
                # packed/sparse-switch
                if (op_value == 0x2B or op_value == 0x2C) and len(
                    i.childs
                ) > 1:
                    values = i.get_special_ins(idx).get_values()
                    content += "[ D:%s " % (i.childs[0][2].get_name())
                    content += (
                        " ".join(
                            "%d:%s"
                            % (values[j], i.childs[j + 1][2].get_name())
                            for j in range(0, len(i.childs) - 1)
                        )
                        + " ]"
                    )
                else:
                    if len(i.childs) == 2:
                        content += "[ {} ".format(
                            i.childs[0][2].get_name(),
                        )
                        content += (
                            " ".join(
                                "%s" % c[2].get_name() for c in i.childs[1:]
                            )
                            + " ]"
                        )
                    else:
                        content += (
                            "[ "
                            + " ".join(
                                "%s" % c[2].get_name() for c in i.childs
                            )
                            + " ]"
                        )
            body.append(content)
            idx += ins.get_length()
    return body
