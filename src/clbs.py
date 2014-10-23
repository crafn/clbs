import platform, os, sys

# Build environment
# Passed to buildInfo(..) in build.clbs
class Env:
    tag= "" # Name supplied by command line
    os= "" # "windows" or "linux"
    arch= "x64" # @todo Auto-detect

class Project:
    name= "default"
    src= [] # Paths to source files
    flags= [] # Flags to compiler
    defines= [] # Macro defines to compiler
    links= []
    targetdir= "."
    compiler= "g++"
    type= "exe" # "exe" or "lib"

def fail(msg):
    print msg
    sys.exit(1)

def msg(m):
    print m

def buildProject(env, p):
    arg_str= ""

    # Compiler flags
    for f in p.flags:
        arg_str += " -" + f

    # Macro defines
    for d in p.defines:
        arg_str += " -D" + d

    # Source files
    arg_str += " " + " ".join(p.src)

    # Links
    for l in p.links:
        arg_str += " -l" + l

    # Output name
    arg_str += " -o " + p.targetdir + "/" + p.name + "_" + env.tag

    # Issue compilation command
    compile_cmd= p.compiler + arg_str
    msg(compile_cmd)
    os.system(compile_cmd)

def build(args):
    build_file_src= ""
    try:
        file= open("build.clbs", "r")
        build_file_src= file.read()
    except:
        fail("Couldn't read build.clbs")

    # @todo Some restrictions!
    exec(build_file_src)

    if len(args) < 1:
        fail("Too few arguments")
    env= Env()
    env.tag= args[0]
    env.os= platform.system().lower()
    build_info= buildInfo(env)
    
    if isinstance(build_info, Project):
        buildProject(env, build_info)
    else:
        fail("buildInfo returned invalid type: " + type(build_info).__name__)

