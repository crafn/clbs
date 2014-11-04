import atexit, operator, os, platform, sys, time
import multiprocessing as mp
import Queue
from cache import *
from interface import *
from util import *

def compilerJob(out_queue, in_queue):
    while True:
        id= None
        cmd= None
        msg= None
        try:
            input= in_queue.get_nowait()
            id= input[0]
            cmd= input[1]
            msg= input[2]
        except Queue.Empty:
            return
        except Exception, e:
            print("clbs: internal error: " + str(e))
            sys.exit(1)

        print("clbs: " + msg)
        ret= run(cmd)
        out_queue.put((id, ret))

## Builds outdated parts of a project
# @param b_outdated_files A set of paths to outdated files in the whole build
# @param force_build Needed in case of rebuilt lib with only impl changes
def buildProject(env, p, cache, b_outdated_files, job_count, force_build):
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
                arg_str += " -I\"" + i + "\""
            for d in p.defines:
                arg_str += " -D" + d
            compile_cmd= p.compiler + arg_str
            msg= src_path
            if env.verbose:
                msg += "\n" + compile_cmd
            in_queue.put((len(src_paths), compile_cmd, msg))
            src_paths.append(src_path)

        # Start compilation jobs
        ## @todo Parallelize compiles between projects
        out_queue= mp_mgr.Queue(maxsize= len(src_paths))
        compiler_pool= mp.Pool(processes= job_count)
        for x in range(job_count):
            compiler_pool.apply_async(
                    compilerJob,
                    (out_queue, in_queue))
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
                if not dep_path in fileRevDeps:
                    fileRevDeps[dep_path]= []
                fileRevDeps[dep_path].append(src_path)

        if p.type == "obj":
            if len(p.links) != 0:
                fail("@todo links for \"obj\" projects")
            return True # Create only object files

        log("linking " + p.name)
        # Remove old target so project isn't considered ready if link fails
        ## @todo Remove tiny window when all is compiled but old target exists,
        #        or add target to fileBuildTimes
        rmFile(targetPath(p))

        arg_str= ""
        for s in p.src:
            arg_str += " " + objFilePath(s, p)
        for l in p.libDirs:
            arg_str += " -L\"" + l + "\""
        for l in p.links:
            if isinstance(l, str):
                arg_str += " -l" + l
            elif isinstance(l, Project):
                if l.type != "obj":
                    fail("Only projects of type \"obj\" can be links")
                for s in l.src:
                    arg_str += " " + objFilePath(s, l)
            elif isinstance(l, list): # Link group
                arg_str += " -Wl,--start-group"
                for member_l in l:
                    arg_str += " -l" + member_l
                arg_str += " -Wl,--end-group"
            else:
                fail("Invalid value in `link`: " + l)

        mkDir(p.targetDir)
        if p.type == "exe":
            arg_str += " -o " + targetPath(p)
            if p.linker != "ld":
                arg_str += " -fuse-ld=" + p.linker
            if "gsplit-dwarf" in p.flags:
                arg_str += " -Wl,--gdb-index" # Indirection of dbg info

            cmd= p.compiler + arg_str
            clog(env.verbose, cmd)
            run_check(cmd)
        elif p.type == "lib":
            arg_str= " rcs " + targetPath(p) + " " + arg_str
            cmd= p.archiver + arg_str
            clog(env.verbose, cmd)
            run_check(cmd)
        else:
            fail("Unsupported project type: " + p.type)

        return True

def buildWithDeps(env, p, cache, b_outdated, job_count, already_built= set()):
    already_built.add(p)
    force_build= False
    for dep_p in p.deps:
        if dep_p in already_built:
            continue
        dep_changed= buildWithDeps(env, dep_p, cache,
                b_outdated, job_count, already_built)
        if dep_changed:
            force_build= True
    if p.type == "exe" or p.type == "lib":
        if not os.path.exists(targetPath(p)):
            force_build= True
    return buildProject(env, p, cache, b_outdated, job_count, force_build)

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

    if p.type == "exe" or p.type == "lib":
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

    env= Env()
    env.os= platform.system().lower()

    # Parse args
    target= "default"
    clean= False
    resetcache= False
    stats= False
    job_count= 1
    for arg in args:
        if arg == "clean":
            clean= True
        elif arg == "resetcache":
            resetcache= True
        elif arg == "stats":
            stats= True
        elif len(arg) > 2 and arg[:2] == "-j":
            job_count= int(arg[2:])
        elif arg == "-v":
            env.verbose= True
        else:
            target= arg
    build= not clean and not resetcache and not stats

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
                clog(env.verbose, "found change in " + file_path)
                b_outdated_files.add(file_path)

                # Add also every file depending on this file
                for compile in cache.compiles.values():
                    rev_deps= compile["fileRevDeps"]
                    if not file_path in rev_deps:
                        continue
                    for dep_path in rev_deps[file_path]:
                        b_outdated_files.add(dep_path)

        buildWithDeps(env, project, cache, b_outdated_files, job_count)
    elif resetcache:
        log("resetcache")
        cache= Cache()
    elif stats:
        log("most included")
        counts= {}
        for p in p_dep_cluster:
            rev_deps= cache.compiles[p._compileHash]["fileRevDeps"]
            for path, rev_deps in rev_deps.items():
                if path not in counts:
                    counts[path]= 0
                counts[path] += len(rev_deps)
        
        top= sorted(counts.items(), key=operator.itemgetter(1))
        for path, count in top:
            if count <= 1:
                continue
            log(path + ": " + str(count))
    elif clean:
        for p in p_dep_cluster:
            cleanProject(env, p, cache)

