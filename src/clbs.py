import atexit, os, platform, sys
from cache import *
from interface import *
from util import *

def run(cmd):
    print(cmd)
    ret= os.system(cmd)
    if ret != 0:
        fail("clbs: build failed")

def buildProject(env, p, cache):
    log("building " + p.name)
    mkDir(p.tempDir)

    # Compile all source files to object files
    for src_path in p.src:
        if not outdated(src_path, p.name, cache):
            continue;
        arg_str= ""
        arg_str += " -c" # No linking at this phase
        for f in p.flags:
            arg_str += " -" + f
        for d in p.defines:
            arg_str += " -D" + d
        arg_str += " " + src_path
        arg_str += " -o " + objFilePath(src_path, p)
       
        compile_cmd= p.compiler + arg_str
        run(compile_cmd)
        cache.buildTimes[(src_path, p.name)]= modTime(src_path)

    # Link object files

    arg_str= ""
    for s in p.src:
        arg_str += " " + objFilePath(s, p)
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

def cleanProject(env, p, cache):
    log("cleaning " + p.name)
    for src_path in p.src:
        obj_path= objFilePath(src_path, p)
        rmFile(obj_path)
        del cache.buildTimes[(src_path, p.name)]
    rmEmptyDir(p.tempDir)

    rmFile(targetPath(p))

def build(args):
    build_file_src= ""
    try:
        with open("build.clbs", "r") as file:
            build_file_src= file.read()
    except:
        fail("Couldn't read build.clbs")

    # @todo Some restrictions!
    exec build_file_src in globals(), locals()

    target= "default"
    clean= False
    upd= False
    build= len(args) == 0
    for arg in args:
        if arg == "clean":
            clean= True
        elif arg == "upd":
            upd= True
        else:
            target= arg
            build= True

    env= Env()
    env.target= target
    env.os= platform.system().lower()
    build_info= buildInfo(env)

    cache= loadCache()
    atexit.register(lambda: writeCache(cache))
    if upd:
        updateCache(cache, build_info)

    if isinstance(build_info, Project):
        if not clean:
            buildProject(env, build_info, cache)
        else:
            cleanProject(env, build_info, cache)
    else:
        fail("buildInfo returned invalid type: " + type(build_info).__name__)

