import cPickle, hashlib, os, sys
from files import *

def fail(msg):
	print("clbs: " + msg)
	sys.exit(1)

def log(msg):
	print("clbs: " + msg)

## Conditional log
def clog(condition, msg):
	if condition:
		print("clbs: " + msg)

def run(cmd):
    ret= os.system(cmd)
    if ret != 0:
        fail("build failed")

## Finds paths to files in dir tree
def findFiles(dir_path, patterns):
	if not isinstance(patterns, list):
		patterns= [patterns]
	paths= []
	for rootdir, dirs, files in os.walk(dir_path):
		for p in patterns:
			for f in fnmatch.filter(files, p):
				paths.append(rootdir + "/" + f)
	return paths

def findNotMatching(lst, patterns):
	if not isinstance(patterns, list):
		patterns= [patterns]
	result= []
	for s in lst:
		match= False
		for p in patterns:
			if fnmatch.fnmatch(s, p):
				match= True
				break
		if not match:
			result.append(s)
	return result

def filenamize(str):
	return "".join([x if x.isalnum() else "_" for x in str])

def mkDir(path):
	if os.path.exists(path):
		return
	try:
		os.makedirs(path)
	except Exception, e:
		fail("mkDir(" + path + ") failed: " + str(e)) 

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

def objHash(obj):
	return hashlib.md5(cPickle.dumps(obj)).hexdigest()[0:8]

def clearQueue(q):
	while not q.empty():
		try:
			q.get_nowait()
		except:
			pass
