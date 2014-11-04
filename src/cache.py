import os
import cPickle
from files import *
from util import *
from interface import *

## Information preserved between builds
class Cache:
	compiles= {} # Maps compileHash to dictionary containing:
		# fileBuildTimes= {} # Maps file_path to last build time
		# fileRevDeps= {} # Maps file_path to list of dependents

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
