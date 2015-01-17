import os
import cPickle
from files import *
from util import *
from interface import *

## Information preserved between builds
class Cache:
	## @todo Organize so that file names are not stored so many times.
	##       Can have significant impact on load and save.
	compiles= {} # Maps compileHash to dictionary containing:
		# fileBuildTimes= {} # Maps file_path to last build time
		# fileRevDeps= {} # Maps file_path to list of dependents
		# headerPaths= {} # List of header files

def cachePath():
	return "./clbs.cache"

def writeCache(env, cache):
	clog(env.verbose, "Writing cache")
	try:
		with open(cachePath(), "wb") as file:
			cPickle.dump(cache.compiles, file, protocol= cPickle.HIGHEST_PROTOCOL)
	except:
		fail("Unable to write cache file")
	clog(env.verbose, "Writing cache completed")

def loadCache(env):
	clog(env.verbose, "Loading cache")
	cache= Cache()
	if os.path.exists(cachePath()):
		try:
			with open(cachePath(), "rb") as file:
				cache.compiles= cPickle.load(file)
				clog(env.verbose, "Loading cache completed")
				return cache
		except EOFError, e:
			fail("Unexpected end of cache file")
		except Exception, e:
			fail("Unable to load cache file: " + str(e))
	else:
		return cache

def outdated(file_path, cpl_hash, cache):
	if not cpl_hash in cache.compiles:
		return True

	compile= cache.compiles[cpl_hash]
	## @todo Add checksum check
	if not file_path in compile["fileBuildTimes"]:
		return True
	if compile["fileBuildTimes"][file_path] < modTime(file_path):
		return True
	return False
