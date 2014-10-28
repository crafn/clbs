import atexit, os, platform, sys, time
import multiprocessing as mp
import Queue
from cache import *
from interface import *
from util import *

def compilerJob(out_queue, in_queue):
    while True:
        id= None
        cmd= None
        try:
            input= in_queue.get_nowait()
            id= input[0]
            cmd= input[1]
        except Queue.Empty:
            return
        except:
            raise "Queue error"

        print(cmd)
        ret= os.system(cmd)
        out_queue.put((id, ret))
        
## Builds outdated parts of a project
# @param b_outdated_files A set of paths to outdated files in the whole build
# @param force_build Needed in case of rebuilt lib with only impl changes
def buildProject(env, p, cache, b_outdated_files, force_build):
    mkDir(p.tempDir)

    # Explicitly or implicitly outdated files of the project
    outdated_files= []
    for path in b_outdated_files:
        if path in p.src or path in p.headers: 
            outdated_files.append(path)

    if len(outdated_files) == 0 and not force_build:
        log("unchanged " + p.name)
        return False
    else:
        log("building " + p.name)
        if not p._compileHash in cache.compiles:
            cache.compiles[p._compileHash]= { 
                "fileBuildTimes": {},
                "fileRevDeps": {}
            }

        # Set headers to updated and sources to outdated
        # This ensures that if build fails halfways, the correct source
        # files will be compiled on next build
        for file_path in outdated_files:
            cpl_time= 0
            if file_path in p.headers:
                cpl_time= modTime(file_path)
            compile= cache.compiles[p._compileHash]
            compile["fileBuildTimes"][file_path]= cpl_time

        # Set up compilation command queue
        mp_mgr= mp.Manager()
        in_queue= mp_mgr.Queue(maxsize= len(outdated_files))
        src_paths= []
        for file_path in outdated_files:
            if not file_path in p.src:
                continue
            src_path= file_path
            arg_str= ""
            arg_str += " -c" # No linking at this phase
            arg_str += " " + src_path
            arg_str += " -MMD" # Dep generation
            arg_str += " -o " + objFilePath(src_path, p)
            for f in p.flags:
                arg_str += " -" + f
            for i in p.includeDirs:
                arg_str += " -I" + i
            for d in p.defines:
                arg_str += " -D" + d
            compile_cmd= p.compiler + arg_str
            in_queue.put((len(src_paths), compile_cmd))
            src_paths.append(src_path)

        # Start compilation jobs
        ## @todo job count from command line
        job_count= 4
        out_queue= mp_mgr.Queue(maxsize= len(src_paths))
        compiler_pool= mp.Pool(processes= job_count)
        for x in range(job_count):
            compiler_pool.apply_async(compilerJob, (out_queue, in_queue))
        compiler_pool.close()

        # Read output from compilation jobs
        cpl_count= 0
        while cpl_count < len(src_paths):
            out= out_queue.get()
            id= out[0]
            success= out[1] == 0
            src_path= src_paths[id]

            if success:
                cpl_count += 1
            else:
                clearQueue(in_queue)
                compiler_pool.join()
                fail("compilation failed")

            # Parse generated dependency file

            dep_file_path= (p.tempDir + "/" + str(p._compileHash) + "_"
                        + filenamize(src_path) + ".d")
            dep_paths= []
            try:
                    contents= None
                    with open(dep_file_path, "rb") as file:
                            contents= file.read()
                    ## @todo Support spaces in filenames :---D
                    for word in contents.split(" "):
                            word= word.strip()
                            if len(word) <= 1: # Handle `\`
                                    continue
                            if word.endswith(":"): # Handle `file:`
                                    continue
                            dep= "./" + word
                            if dep == src_path:
                                    continue # File obviously depends on itself
                            dep_paths.append(dep)
            except Exception, e:
                    fail("Couldn't parse dependency file " +
                            dep_file_path + ": " + str(e))
            os.remove(dep_file_path)

            # Update cache

            compile= cache.compiles[p._compileHash]
            compile["fileBuildTimes"][src_path]= modTime(src_path)

            fileRevDeps= compile["fileRevDeps"]
            if not src_path in fileRevDeps:
                fileRevDeps[src_path]= []

            # Remove old dependencies
            # Note that `fileRevDeps` has the reverse dependencies
            for rev_path, rev_deps in fileRevDeps.items():
                if rev_path in dep_paths:
                    if src_path in rev_deps:
                        rev_deps.remove(src_path) 
            # Add new dependencies
            for dep_path in dep_paths:
                #vlog("dep " + dep_path)
                if not dep_path in fileRevDeps:
                    fileRevDeps[dep_path]= []
                fileRevDeps[dep_path].append(src_path)

        # Link object files

        arg_str= ""
        for s in p.src:
            arg_str += " " + objFilePath(s, p)
        for l in p.libDirs:
            arg_str += " -L" + l
        for l in p.links:
            arg_str += " -l" + l

        mkDir(p.targetDir)
        if p.type == "exe":
            arg_str += " -o " + targetPath(p)
            run(p.compiler + arg_str)
        elif p.type == "lib":
            arg_str= " rcs " + targetPath(p) + " " + arg_str
            run(p.archiver + arg_str)
        else:
            fail("Unsupported project type: " + p.type)

        ## @todo Add target to fileBuildTimes

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
        if p == project:
            fail("Project depends on itself: " + project.name)
        findProjectDepCluster(result, p) # Deepest deps first
    if not project in result:
        result.append(project)

def runClbs(args):
    timer= time.time()
    atexit.register(lambda: log(str(round(time.time() - timer, 2)) + "s"))

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
    for arg in args:
        if arg == "clean":
            clean= True
        elif arg == "resetcache":
            resetcache= True
        else:
            target= arg
    build= not clean and not resetcache

    env= Env()
    env.os= platform.system().lower()
    project= buildInfo(env, target)

    cache= loadCache()
    atexit.register(lambda: writeCache(cache))

    # Preprocess all projects in dep cluster
    p_dep_cluster= []
    findProjectDepCluster(p_dep_cluster, project) 
    for p in p_dep_cluster:
        # Omitting include- and libdirs because adding include or lib
        # shouldn't usually cause recompilation
        p._compileHash= objHash(
            (p.name,
            p.flags,
            p.defines,
            p.tempDir,
            p.compiler,
            p.archiver))

    if build:
        # Find all (directly or indirectly) outdated files of the build
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

