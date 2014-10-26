import cPickle, hashlib, os, sys
from files import *

def fail(msg):
	print("clbs: " + msg)
	sys.exit(1)

def log(msg):
	print("clbs: " + msg)

## Verbose log
def vlog(msg):
	print("clbs: " + msg)

def run(cmd):
    print(cmd)
    ret= os.system(cmd)
    if ret != 0:
        fail("clbs: build failed")

## Finds paths to files in dir tree
def findFiles(dir_path, patterns):
	paths= []
	for rootdir, dirs, files in os.walk(dir_path):
		for p in patterns:
			for f in fnmatch.filter(files, p):
				paths.append(rootdir + "/" + f)
	return paths

def filenamize(str):
	return "".join([x if x.isalnum() else "_" for x in str])

def mkDir(path):
	if not os.path.exists(path):
		os.mkdir(path)

def rmFile(path):
	if fnmatch.fnmatch(path, "*.c*"):
		fail("DEBUG: Trying to delete file: " + path)
	elif os.path.exists(path):
		os.remove(path)

## Removes only empty directories
def rmEmptyDir(path):
	if os.path.exists(path) and not os.listdir(path):
		os.rmdir(path)

def modTime(path):
	if os.path.exists(path):
		return os.stat(path).st_mtime
	else:
		return 0

def objFilePath(src_file_path, p):
    return (p.tempDir + "/" + str(p._compileHash) + "_"
            + filenamize(src_file_path) + ".o")

def targetPath(p):
    if p.type == "exe":
        return p.targetDir + "/" + p.name
    elif p.type == "lib":
        return p.targetDir + "/lib" + p.name + ".a"
    else:
        fail("Unsupported project type: " + p.type)

## Finds paths to dependencies of a file
# Dependencies include all deps of deps
# @note Performs file io and compiler invokation
def findFileDependencies(path, p):
	# Generate make-like dependency file
	dep_file_path= (p.tempDir + "/" + str(p._compileHash) + "_"
			+ filenamize(path) + ".d")
	cmd= p.compiler + " -MM " + path + " -MF " + dep_file_path
	for i in p.includeDirs:
		cmd += " -I" + i
	run(cmd)

	# Parse the file
	deps= []
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
			if dep == path:
				continue # File obviously depends on itself
			deps.append(dep)
	except Exception, e:
		fail("Couldn't parse dependency file " + dep_file_path + ": " + str(e))

	os.remove(dep_file_path)
	return deps

def objHash(obj):
	return hashlib.md5(cPickle.dumps(obj)).hexdigest()[0:8]

