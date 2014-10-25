import atexit, os, platform, sys
from cache import *
from interface import *
from util import *

def buildProject(env, p, cache):
    mkDir(p.tempDir)

    # Find list of outdated source files
    outdated_src= []
    for src_path in p.src:
        if outdated(src_path, p._compileHash, cache):
            outdated_src.append(src_path)
 
    if len(outdated_src) == 0:
        log("unchanged " + p.name)
    else:
        log("building " + p.name)

        # Update dependencies
        for src_path in outdated_src:
            if not p._compileHash in cache.compiles:
                cache.compiles[p._compileHash]= { 
                        "srcBuildTimes": {},
                        "srcRevDeps": {}
                 }
            compile= cache.compiles[p._compileHash]
            srcRevDeps= compile["srcRevDeps"]
            dep_paths= findFileDependencies(src_path, p)
            # Remove old dependencies
            # Note that `srcRevDeps` has the reverse dependencies
            for rev_src, rev_deps in srcRevDeps.items():
                if rev_src in dep_paths:
                    if src_path in rev_deps:
                        rev_deps.remove(src_path) 
            # Add new dependencies
            for dep_path in dep_paths:
                log("dep " + dep_path)
                if not dep_path in srcRevDeps:
                    srcRevDeps[dep_path]= []
                srcRevDeps[dep_path].append(src_path)

        # Compile all source files to object files
        for src_path in outdated_src:
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

            # Add compilation to cache
            compile= cache.compiles[p._compileHash]
            compile["srcBuildTimes"][src_path]= modTime(src_path)
       
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
    # @todo Clean obsolete files left after changing compileHash
    for src_path in p.src:
        obj_path= objFilePath(src_path, p)
        rmFile(obj_path)
        if p._compileHash in cache.compiles:
            compile= cache.compiles[p._compileHash]
            if src_path in compile["srcBuildTimes"]:
                del compile["srcBuildTimes"][src_path]
            #del cache.compiles[p._compileHash]["srcDeps"][src_path]
    rmEmptyDir(p.tempDir)

    rmFile(targetPath(p))

def runClbs(args):
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
    resetcache= False
    upd= False
    for arg in args:
        if arg == "clean":
            clean= True
        elif arg == "resetcache":
            resetcache= True
        elif arg == "upd":
            upd= True
        else:
            target= arg
    build= not clean and not resetcache and not upd

    env= Env()
    env.target= target
    env.os= platform.system().lower()
    build_info= buildInfo(env)

    cache= loadCache()
    atexit.register(lambda: writeCache(cache))

    if isinstance(build_info, Project):
        build_info._compileHash= objHash(
                (build_info.flags,
                build_info.defines,
                build_info.links,
                build_info.tempDir,
                build_info.compiler,
                build_info.archiver))
        if clean:
            cleanProject(env, build_info, cache)

        if resetcache:
            log("resetcache")
            cache= Cache()

        if upd:
            updateCache(cache, build_info)
 
        if build:
            buildProject(env, build_info, cache)
    else:
        fail("buildInfo returned invalid type: " + type(build_info).__name__)

