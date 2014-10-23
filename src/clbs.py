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

def objFilePath(p, src_file_path):
    return (p.tempdir + "/" + p.name + "_"
            + filenamize(src_file_path) + ".o")

def buildProject(env, p):
    log("clbs: building " + p.name)
    mkDir(p.tempdir)
    
    #
    # Compile all source files to object files
    #

    for src_path in p.src:
        arg_str= ""
        arg_str += " -c" # No linking at this phase

        # Compiler flags
        for f in p.flags:
            arg_str += " -" + f

        # Macro defines
        for d in p.defines:
            arg_str += " -D" + d

        # Source file
        arg_str += " " + src_path

        # Compilation output
        cpl_out_path= objFilePath(p, src_path)
        arg_str += " -o " + cpl_out_path
       
        # Issue compilation
        compile_cmd= p.compiler + arg_str
        run(compile_cmd)

    #
    # Link object files
    #

    arg_str= ""

    # Project object files
    for s in p.src:
        arg_str += " " + objFilePath(p, s)

    # Project links
    for l in p.links:
        arg_str += " -l" + l

    # Output 
    link_out_path= ""
    if p.type == "exe":
        link_out_path= p.targetdir + "/" + p.name
    elif p.type == "lib":
        link_out_path= p.targetdir + "/lib" + p.name + ".a"
    else:
        fail("Unsupported project type: " + p.type)
   
   # Issue linker
    if p.type == "exe":
        arg_str += " -o " + link_out_path
        run(p.compiler + arg_str)
    elif p.type == "lib":
        arg_str= " rcs " + link_out_path + " " + arg_str
        run(p.archiver + arg_str)
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

