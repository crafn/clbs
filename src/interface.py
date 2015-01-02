## Build environment
# Passed to buildInfo(..) in build.clbs
class Env:
	def __init__(self):
		self.os= "" ## "windows" or "linux"
		self.arch= "x64" ## @todo Auto-detect
		self.verbose= False

## Contains information on how to build a project
# `buildInfo` in build.clbs should return a `Project` object
class Project:
	def __init__(self):
		self.name= "default"
		self.headers= [] ## Paths to header files
		self.src= [] ## Paths to source files
		self.deps= [] ## List containing other projects
		self.flags= [] ## Flags to compiler
		self.defines= [] ## Macro defines to compiler
		self.includeDirs= [] ## Include directories
		self.libDirs= [] ## Library directories
		self.links= [] ## Statically linked libraries
		self.targetDir= "."
		self.tempDir= "./obj"
		self.compiler= "g++"
		self.linker= "ld" # "ld" or "gold"
		self.archiver= "ar"
		self.type= "exe" ## "exe", "lib", "obj" or "dll"
		# Private
		self._compileHash= 0 # Unique for every project and compile cmd cfg
