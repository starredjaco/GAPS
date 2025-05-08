import sys
import logging
import os
import click

from importlib import metadata

from gaps.run.gaps_run import GAPSRUN
from gaps.static.gaps import GAPS

__version__ = metadata.version("gaps")

###############################################################################
# LOGGING
###############################################################################

LOG = logging.getLogger("gaps")
logging.basicConfig(format="%(message)s")

###############################################################################
# CODE
###############################################################################


@click.group()
@click.version_option(
    __version__, "-v", "--version", is_flag=True, message="%(version)s"
)
@click.pass_context
def cli(ctx):
    """GAPS: Graph-based Automated Path Synthesizer"""
    pass


@cli.command("static")
@click.option(
    "-i",
    "--input",
    type=click.Path(exists=True),
    help="APK/DEX path file to disassemble",
    required=True,
)
@click.option(
    "-m", "--method", type=str, help="Target method to generate paths from"
)
@click.option(
    "-cls",
    "--class_name",
    type=str,
    help="Target class to generate paths from",
)
@click.option(
    "-p_cls",
    "--parent_class",
    type=str,
    help="Find target method invocation in a specific parent class",
)
@click.option(
    "-sig",
    "--signature",
    type=str,
    help="Target method signature in Smali format to build paths for it",
)
@click.option(
    "-seed",
    "--seed_file",
    type=click.Path(exists=True),
    help="Path to the file containing seed signatures",
)
@click.option(
    "-custom_seed",
    "--custom_seed_file",
    type=click.Path(exists=True),
    help="Path to the file containing custom seed signatures",
)
@click.option(
    "-o",
    "--output",
    type=str,
    help="Path to output directory",
)
@click.option(
    "-cond",
    "--conditional",
    is_flag=True,
    help="Generate paths that satisfy conditional statements",
)
@click.option(
    "-l",
    "--path_limit",
    type=int,
    default=1000,
    help="Set an upper bound to the total number of paths reconstructed for each query (default: 1000)",
)
@click.option(
    "-up",
    "--unconstrained-paths",
    is_flag=True,
    help="Generate paths without constraints",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-d", "--debug", is_flag=True, help="Enable debug output")
def static(
    input,
    method,
    class_name,
    parent_class,
    signature,
    seed_file,
    custom_seed_file,
    output,
    conditional,
    path_limit,
    unconstrained_paths,
    verbose,
    debug,
):
    """
    Initializes and starts the path finding process.
    """

    log_level = logging.WARNING
    if verbose:
        log_level = logging.INFO
    elif debug:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level)
    LOG.setLevel(log_level)

    if not input:
        LOG.error("[-] ERROR: NO INPUT")
        sys.exit(1)

    LOG.info(f"[+] LOADING {input}")

    if method:
        LOG.info(f"[+] LOOKING FOR {method}")
    if class_name:
        LOG.info(f"[+] LOOKING IN {class_name}")
    if parent_class:
        LOG.info(f"[+] USED IN {parent_class}")
    if signature:
        LOG.info(f"[+] LOOKING FOR {signature}")
    if seed_file:
        LOG.info(f"[+] USING SEED FILE {seed_file}")
    if conditional:
        LOG.info("[+] CONDITIONAL PATHS GENERATION")
    if path_limit <= 0:
        LOG.error("[-] NO PATHS CAN BE GENERATED: MAX PATHS <= 0")
    if unconstrained_paths:
        LOG.info("[+] UNCONSTRAINED PATH RECONSTRUCTION")
        path_limit = sys.maxsize
    if path_limit:
        LOG.info(f"[+] PATH LIMIT: {path_limit}")
    default_output = "./out"
    if not output:
        output = default_output
    LOG.info(f"[+] OUTPUT DIRECTORY: {output}")
    if not os.path.exists(output):
        os.mkdir(output)

    GAPS(
        input,
        method,
        class_name,
        parent_class,
        signature,
        seed_file,
        custom_seed_file,
        output,
        conditional,
        log_level,
        path_limit,
    )


@cli.command("run")
@click.option(
    "-i",
    "--apk",
    help="APK path file to run",
    required=True,
)
@click.option(
    "-instr",
    "--instructions",
    help="Path to the instruction file",
    required=True,
)
@click.option("-o", "--output", help="Path to the output directory")
@click.option(
    "-frida",
    "--frida",
    is_flag=True,
    help="Use Frida for dynamic analysis",
    default=False,
)
@click.option(
    "-ms",
    "--manual-setup",
    is_flag=True,
    help="Introduce a manual setup",
    default=False,
)
@click.option(
    "-t",
    "--target",
    is_flag=True,
    help="Target a specific method",
)
def run(apk, instructions, output, frida, manual_setup, target):
    """
    Initializes and starts the path finding process.
    """

    LOG.info(f"[+] LOADING {apk}")

    default_output = "./out"
    if not output:
        output = default_output

    if not os.path.exists(output):
        os.mkdir(output)

    instructions_dir = os.path.dirname(instructions)
    LOG.info(f"[+] INSTRUCTIONS DIRECTORY: {instructions_dir}")

    gaps_run = GAPSRUN(apk, output, manual_setup, frida)
    gaps_run.run(instructions, target, instructions_dir)


@cli.command("hybrid")
@click.option(
    "-i",
    "--input",
    type=click.Path(exists=True),
    help="APK/DEX path file to disassemble",
    required=True,
)
@click.option(
    "-m", "--method", type=str, help="Target method to generate paths from"
)
@click.option(
    "-cls",
    "--class_name",
    type=str,
    help="Target class to generate paths from",
)
@click.option(
    "-p_cls",
    "--parent_class",
    type=str,
    help="Find target method invocation in a specific parent class",
)
@click.option(
    "-sig",
    "--signature",
    type=str,
    help="Target method signature in Smali format to build paths for it",
)
@click.option(
    "-seed",
    "--seed_file",
    type=click.Path(exists=True),
    help="Path to the file containing seed signatures",
)
@click.option(
    "-custom_seed",
    "--custom_seed_file",
    type=click.Path(exists=True),
    help="Path to the file containing custom seed signatures",
)
@click.option(
    "-o",
    "--output",
    type=str,
    help="Path to output directory",
)
@click.option(
    "-cond",
    "--conditional",
    is_flag=True,
    help="Generate paths that satisfy conditional statements",
)
@click.option(
    "-l",
    "--path_limit",
    type=int,
    default=1000,
    help="Set an upper bound to the total number of paths reconstructed for each query (default: 1000)",
)
@click.option(
    "-up",
    "--unconstrained-paths",
    is_flag=True,
    help="Generate paths without constraints",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-d", "--debug", is_flag=True, help="Enable debug output")
@click.option(
    "-frida",
    "--frida",
    is_flag=True,
    help="Use Frida for dynamic analysis",
    default=True,
)
@click.option(
    "-ms",
    "--manual-setup",
    is_flag=True,
    help="Introduce a manual setup",
    default=True,
)
@click.option(
    "-t",
    "--target",
    is_flag=True,
    help="Target a specific method",
)
def hybrid(
    input,
    method,
    class_name,
    parent_class,
    signature,
    seed_file,
    custom_seed_file,
    output,
    conditional,
    path_limit,
    unconstrained_paths,
    verbose,
    debug,
    frida,
    manual_setup,
    target,
):
    """
    Initializes and starts the path finding process.
    """

    static(
        input,
        method,
        class_name,
        parent_class,
        signature,
        seed_file,
        custom_seed_file,
        output,
        conditional,
        path_limit,
        unconstrained_paths,
        verbose,
        debug,
    )

    file_name = os.path.splitext(os.path.basename(input))[0]
    instructions = os.path.join(output, f"{file_name}-instr.json")

    run(input, instructions, output, frida, manual_setup, target)


if __name__ == "__main__":
    cli()
