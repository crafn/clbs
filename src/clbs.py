import os, sys

class Project:
    name= "default"
    src= [] # Paths to source files
    flags= [] # Flags to compiler
    defines= [] # Macro defines to compiler
    targetdir= "."
    compiler= "g++"
    type= "exe" # "exe" or "lib"

def fail(msg):
    print msg
    sys.exit(1)

def msg(m):
    print m

def buildProject(cfg, p):
    arg_str= ""

    # Compiler flags
    for f in p.flags:
        arg_str += " -" + f

    # Macro defines
    for d in p.defines:
        arg_str += " -D" + d

    # Source files
    arg_str += " " + " ".join(p.src)

    # Output name
    arg_str += " -o " + p.targetdir + "/" + p.name + "_" + cfg

    # Issue compilation command
    compile_cmd= p.compiler + arg_str
    msg(compile_cmd)
    os.system(compile_cmd)

def build(args):
    if len(args) < 1:
        fail("Too few arguments")
    cfg= args[0]

    build_file_src= ""
    try:
        file= open("build.clbs", "r")
        build_file_src= file.read()
    except:
        fail("Couldn't read build.clbs")

    # @todo Some restrictions!
    exec(build_file_src)
    build_info= buildInfo(cfg)
    
    if isinstance(build_info, Project):
        buildProject(cfg, build_info)
    else:
        fail("buildInfo returned invalid type: " + type(build_info).__name__)

