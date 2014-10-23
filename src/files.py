import fnmatch
import os

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
