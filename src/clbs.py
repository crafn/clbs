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
    targetDir= "."
    tempDir= "./obj"
    compiler= "g++"
    archiver= "ar"
    type= "exe" # "exe" or "lib"

def run(cmd):
    print(cmd)
    ret= os.system(cmd)
    if ret != 0:
        fail("clbs: build failed")

def objFilePath(p, src_file_path):
    return (p.tempDir + "/" + p.name + "_"
            + filenamize(src_file_path) + ".o")

def targetPath(p):
    if p.type == "exe":
        return p.targetDir + "/" + p.name
    elif p.type == "lib":
        return p.targetDir + "/lib" + p.name + ".a"
    else:
        fail("Unsupported project type: " + p.type)
 
def buildProject(env, p):
    log("building " + p.name)
    mkDir(p.tempDir)
    
    # Compile all source files to object files
    for src_path in p.src:
        arg_str= ""
        arg_str += " -c" # No linking at this phase
        for f in p.flags:
            arg_str += " -" + f
        for d in p.defines:
            arg_str += " -D" + d
        arg_str += " " + src_path
        arg_str += " -o " + objFilePath(p, src_path)
       
        compile_cmd= p.compiler + arg_str
        run(compile_cmd)

    # Link object files

    arg_str= ""
    for s in p.src:
        arg_str += " " + objFilePath(p, s)
    for l in p.links:
        arg_str += " -l" + l

    if p.type == "exe":
        arg_str += " -o " + targetPath(p)
        run(p.compiler + arg_str)
    elif p.type == "lib":
        arg_str= " rcs " + targetPath(p) + " " + arg_str
        run(p.archiver + arg_str)
    else:
        fail("Unsupported project type: " + p.type)

def cleanProject(env, p):
    log("cleaning " + p.name)
    for src_path in p.src:
        obj_path= objFilePath(p, src_path)
        rmFile(obj_path)
    rmEmptyDir(p.tempDir)

    rmFile(targetPath(p))

def build(args):
    build_file_src= ""
    try:
        file= open("build.clbs", "r")
        build_file_src= file.read()
    except:
        fail("Couldn't read build.clbs")

    # @todo Some restrictions!
    exec(build_file_src)

    tag= "default"
    clean= False
    for arg in args:
        if arg == "clean":
            clean= True
        else:
            tag= arg

    env= Env()
    env.tag= tag
    env.os= platform.system().lower()
    build_info= buildInfo(env)

    if isinstance(build_info, Project):
        if not clean:
            buildProject(env, build_info)
        else:
            cleanProject(env, build_info)
    else:
        fail("buildInfo returned invalid type: " + type(build_info).__name__)

