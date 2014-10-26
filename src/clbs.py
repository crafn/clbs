import atexit, os, platform, sys
from cache import *
from interface import *
from util import *

## Builds outdated parts of a project
# @param b_outdated_files A set of paths to outdated files in the whole build
# @param force_build Needed in case of rebuilt lib with only impl changes
def buildProject(env, p, cache, b_outdated_files, force_build):
    mkDir(p.tempDir)

    outdated_files= []
    for path in b_outdated_files:
        if path in p.src or path in p.headers: 
            outdated_files.append(path)

    if len(outdated_files) == 0 and not force_build:
        log("unchanged " + p.name)
        return False
    else:
        log("building " + p.name)

        # Update dependencies
        for file_path in outdated_files:
            if not p._compileHash in cache.compiles:
                cache.compiles[p._compileHash]= { 
                        "fileBuildTimes": {},
                        "fileRevDeps": {}
                 }
            fileRevDeps= cache.compiles[p._compileHash]["fileRevDeps"]
            if not file_path in fileRevDeps:
                fileRevDeps[file_path]= []
            dep_paths= findFileDependencies(file_path, p)
            # Remove old dependencies
            # Note that `fileRevDeps` has the reverse dependencies
            for rev_path, rev_deps in fileRevDeps.items():
                if rev_path in dep_paths:
                    if file_path in rev_deps:
                        rev_deps.remove(file_path) 
            # Add new dependencies
            for dep_path in dep_paths:
                vlog("dep " + dep_path)
                if not dep_path in fileRevDeps:
                    fileRevDeps[dep_path]= []
                fileRevDeps[dep_path].append(file_path)

        # Find the whole dependency cluster (including outdated files)
        ## @todo Exclude files outside project
        dep_cluster= set()
        fileRevDeps= cache.compiles[p._compileHash]["fileRevDeps"]
        for file_path in outdated_files:
            dep_cluster.add(file_path)
            for dep_path in fileRevDeps[file_path]:
                dep_cluster.add(dep_path)

        # Compile all source files in dep cluster
        for file_path in dep_cluster:
            if not file_path in p.src:
                continue
            src_path= file_path

            arg_str= ""
            arg_str += " -c" # No linking at this phase
            arg_str += " " + src_path
            arg_str += " -o " + objFilePath(src_path, p)
            for f in p.flags:
                arg_str += " -" + f
            for i in p.includeDirs:
                arg_str += " -I" + i
            for d in p.defines:
                arg_str += " -D" + d

            compile_cmd= p.compiler + arg_str
            run(compile_cmd)

        # Update compilation times to cache
        for file_path in dep_cluster:
            compile= cache.compiles[p._compileHash]
            compile["fileBuildTimes"][file_path]= modTime(file_path)
 
        # Link object files
        arg_str= ""
        for s in p.src:
            arg_str += " " + objFilePath(s, p)
        for l in p.libDirs:
            arg_str += " -L" + l
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

        return True

def buildWithDeps(env, p, cache, b_outdated, already_built= set()):
    already_built.add(p)
    force_build= False
    for dep_p in p.deps:
        if dep_p in already_built:
            continue
        dep_changed= buildWithDeps(env, dep_p, cache, b_outdated, already_built)
        if dep_changed:
            force_build= True
    return buildProject(env, p, cache, b_outdated, force_build)

def cleanProject(env, p, cache):
    log("cleaning " + p.name)
    # @todo Clean obsolete files left after changing compileHash
    for src_path in p.src:
        obj_path= objFilePath(src_path, p)
        rmFile(obj_path)
        if p._compileHash in cache.compiles:
            compile= cache.compiles[p._compileHash]
            if src_path in compile["fileBuildTimes"]:
                del compile["fileBuildTimes"][src_path]
    rmEmptyDir(p.tempDir)

    rmFile(targetPath(p))

## Internal func of runClbs
def findProjectDepCluster(result, project):
    for p in project.deps:
        findProjectDepCluster(result, p) # Deepest deps first
    if not project in result:
        result.append(project)

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
    env.os= platform.system().lower()
    project= buildInfo(env, target)

    cache= loadCache()
    atexit.register(lambda: writeCache(cache))

    # Preprocess all projects in dep cluster
    p_dep_cluster= []
    findProjectDepCluster(p_dep_cluster, project) 
    for p in p_dep_cluster:
        p._compileHash= objHash(
            (p.name,
            p.flags,
            p.defines,
            p.includeDirs,
            p.libDirs,
            p.links,
            p.tempDir,
            p.compiler,
            p.archiver))

    if build:
        # Find all (directly or indirectly) outdated files of build
        b_outdated_files= set()
        for p in p_dep_cluster:
            for file_path in p.src + p.headers:
                if not outdated(file_path, p._compileHash, cache):
                    continue
                vlog("found change in " + file_path)
                b_outdated_files.add(file_path)

                # Add also every file depending on this file
                for compile in cache.compiles.values():
                    rev_deps= compile["fileRevDeps"]
                    if not file_path in rev_deps:
                        continue
                    for dep_path in rev_deps[file_path]:
                        b_outdated_files.add(dep_path)

        buildWithDeps(env, project, cache, b_outdated_files)
    elif resetcache:
        log("resetcache")
        cache= Cache()
    else:
        for p in p_dep_cluster:
            if clean:
                cleanProject(env, p, cache)
            if upd:
                updateCache(cache, p)

