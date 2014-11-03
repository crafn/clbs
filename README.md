#clbs

Build system for Project Clover written in Python 2.7

## Installation
### Linux

Install Python 2.7 and git, then

	git clone https://github.com/crafn/clbs.git
	cd clbs
	sudo ./INSTALL

Now clbs can be used in any directory with the command `clbs`

### Windows
TODO

## Usage
Building a project using clbs

	cd directory_containing_build.clbs
	clbs <target> <options>

It's recommended that plain `clbs` without targets and options builds something reasonable.

Common options

	clean    remove objects, libs and executables produced by a former build
	-jx      use x number of parallel compiler processes
	-v       print compilation commands

