import fnmatch
import os
from util import *

# Finds paths to files in dir tree
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

# Removes only empty directories
def rmEmptyDir(path):
	if os.path.exists(path) and not os.listdir(path):
		os.rmdir(path)
