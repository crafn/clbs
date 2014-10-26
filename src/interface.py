## Build environment
# Passed to buildInfo(..) in build.clbs
class Env:
    target= "default" ## Name supplied by command line
    os= "" ## "windows" or "linux"
    arch= "x64" ## @todo Auto-detect

## Contains information on how to build a project
# `buildInfo` in build.clbs should return a `Project` object
class Project:
	name= "default"
	headers= [] ## Paths to header files
	src= [] ## Paths to source files
	deps= [] ## List containing other projects
	flags= [] ## Flags to compiler
	defines= [] ## Macro defines to compiler
	includeDirs= [] ## Include directories
	libDirs= [] ## Library directories
	links= [] ## Statically linked libraries
	targetDir= "."
	tempDir= "./obj"
	compiler= "g++"
	archiver= "ar"
	type= "exe" ## "exe" or "lib"
	# Private
	_compileHash= 0 # Hash from compiler command configuration

