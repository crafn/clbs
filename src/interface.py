## Build environment
# Passed to buildInfo(..) in build.clbs
class Env:
    target= "default" ## Name supplied by command line
    os= "" ## "windows" or "linux"
    arch= "x64" ## @todo Auto-detect

## Contains information on how to build a project
class Project:
	name= "default"
	headers= [] ## Paths to header files
	src= [] ## Paths to source files
	flags= [] ## Flags to compiler
	defines= [] ## Macro defines to compiler
	links= []
	targetDir= "."
	tempDir= "./obj"
	compiler= "g++"
	archiver= "ar"
	type= "exe" ## "exe" or "lib"
	# Private
	_compileHash= 0 # Hash from flags, defines, libs and links

