import platform, os, sys
from files import *

# Build environment
# Passed to buildInfo(..) in build.clbs
class Env:
    tag= "default" # Name supplied by command line
    os= "" # "windows" or "linux"
    arch= "x64" # @todo Auto-detect

class Project:
    name= "default"
    src= [] # Paths to source files
    flags= [] # Flags to compiler
    defines= [] # Macro defines to compiler
    links= []
    targetdir= "."
    tempdir= "./obj"
    compiler= "g++"
    archiver= "ar"
    type= "exe" # "exe" or "lib"

def fail(msg):
    print(msg)
    sys.exit(1)

def log(msg):
    print(msg)

def run(cmd):
    log(cmd)
    ret= os.system(cmd)
    if ret != 0:
        fail("clbs: build failed")

def buildProject(env, p):
    log("clbs: building " + p.name)
    
    arg_str= ""
    if p.type == "lib":
        arg_str += " -c" # No linking

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

    # Compilation output
    cpl_out_path= p.targetdir + "/" + p.name
    if p.type == "lib":
        cpl_out_path += ".o"
    arg_str += " -o " + cpl_out_path
   
    # Issue compilation
    compile_cmd= p.compiler + arg_str
    run(compile_cmd)

    if p.type == "exe":
        pass
    elif p.type == "lib":
        # .o to .a
        ar_cmd= p.archiver + " rcs lib" + p.name + " " + cpl_out_path
        run(ar_cmd)
    else:
        fail("Unsupported project type: " + p.type)

def build(args):
    build_file_src= ""
    try:
        file= open("build.clbs", "r")
        build_file_src= file.read()
    except:
        fail("Couldn't read build.clbs")

    # @todo Some restrictions!
    exec(build_file_src)

    env= Env()
    env.os= platform.system().lower()
    if len(args) >= 1:
        env.tag= args[0]
    build_info= buildInfo(env)
    
    if isinstance(build_info, Project):
        buildProject(env, build_info)
    else:
        fail("buildInfo returned invalid type: " + type(build_info).__name__)

