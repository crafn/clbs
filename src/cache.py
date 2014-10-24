import os
import cPickle
from files import *
from util import *
from interface import *

# Information preserved between builds
class Cache:
	buildTimes= {} # Maps (src_path, cpl_hash) to last build time

def cachePath():
    return "./clbs.cache"

def writeCache(cache):
	#log("Writing cache: ")
	try:
		with open(cachePath(), "wb") as file:
			cPickle.dump(cache.buildTimes, file)
	except:
		fail("Unable to write cache file")

def loadCache():
	#log("Loading cache")
	cache= Cache()
	if os.path.exists(cachePath()):
		try:
			with open(cachePath(), "rb") as file:
				cache.buildTimes= cPickle.load(file)
				return cache
		except:
			fail("Unable to load cache file")
	else:
		return cache

# Makes cache to match with files on disk
def updateCache(cache, build_info):
    if isinstance(build_info, Project):
        p= build_info
        log("updating " + p.name)
        for src_path in p.src:
            t= modTime(objFilePath(src_path, p))
            build_time_key= (src_path, p._compileHash)
            if t == 0:
                if build_time_key in cache.buildTimes:
                    del cache.buildTimes[build_time_key]
            else:
                cache.buildTimes[build_time_key]= t
    else:
        fail("Unknown info type: " + build_info)

def outdated(src_path, cpl_hash, cache):
    # @todo Add checksum check
	if not (src_path, cpl_hash) in cache.buildTimes:
		return True
	if cache.buildTimes[(src_path, cpl_hash)] < modTime(src_path):
		return True
	return False
