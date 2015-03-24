import os
import cPickle
import hashlib
from files import *
from util import *
from interface import *

class BuildTimeInfo:
	cpl_time= 0 # If cpl_time < modTime(file_path) file has been modified after cpl
	checksum= 0 # If cpl_time < modTime(file_path) and checksum != fileChecksum(file_path), must recompile

## Information preserved between builds
class Cache:
	## @todo Organize so that file names are not stored so many times.
	##       Can have significant impact on load and save.
	compiles= {} # Maps compileHash to dictionary containing:
		# fileBuildTimes= {} # Maps file_path to BuildTimeInfo
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

def fileChecksum(path):
	with open(path, "rb") as file:
		data= file.read()
		return hashlib.md5(data).digest()

def outdated(file_path, cpl_hash, cache):
	if not cpl_hash in cache.compiles:
		return True

	compile= cache.compiles[cpl_hash]
	if not file_path in compile["fileBuildTimes"]:
		return True

	build_info= compile["fileBuildTimes"][file_path]
	if build_info.cpl_time < modTime(file_path):
		file_checksum= fileChecksum(file_path)
		if build_info.checksum != file_checksum:
			return True # File has changed
		else:
			return False
	else:
		return False

def newBuildTimeInfo(file_path):
	b= BuildTimeInfo()
	b.cpl_time= modTime(file_path)
	b.checksum= fileChecksum(file_path)
	return b

def outdatedBuildTimeInfo():
	return BuildTimeInfo()
