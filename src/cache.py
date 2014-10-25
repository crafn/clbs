import os
import cPickle
from files import *
from util import *
from interface import *

## Information preserved between builds
class Cache:
	compiles= {} # Maps compileHash to dictionary containing:
		# srcBuildTimes= {} # Maps src_path to last build time
		# srcRevDeps= {} # Maps src_path to list of dependents

def cachePath():
	return "./clbs.cache"

def writeCache(cache):
	#log("Writing cache: ")
	try:
		with open(cachePath(), "wb") as file:
			cPickle.dump(cache.compiles, file)
	except:
		fail("Unable to write cache file")

def loadCache():
	#log("Loading cache")
	cache= Cache()
	if os.path.exists(cachePath()):
		try:
			with open(cachePath(), "rb") as file:
				cache.compiles= cPickle.load(file)
				return cache
		except:
			fail("Unable to load cache file")
	else:
		return cache

# Makes cache to match with files on disk
def updateCache(cache, build_info):
	if isinstance(build_info, Project):
		p= build_info
		compile= cache.compiles[p._compileHash]
		log("updating " + p.name)
		for src_path in p.src:
			t= modTime(objFilePath(src_path, p))
			if t == 0:
				if src_path in compile["srcBuildTimes"]:
					del compile["srcBuildTimes"][src_path]
			else:
				compile["srcBuildTimes"][src_path]= t
	else:
		fail("Unknown info type: " + build_info)

def outdated(src_path, cpl_hash, cache):
	if not cpl_hash in cache.compiles:
		return True

	compile= cache.compiles[cpl_hash]
	## @todo Add checksum check
	if not src_path in compile["srcBuildTimes"]:
		return True
	if compile["srcBuildTimes"][src_path] < modTime(src_path):
		return True
	return False
