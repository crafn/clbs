#clbs

Build system for Project Clover written in Python 2.7

## Installation
Install Python 2.7 and git, then

	git clone https://github.com/crafn/clbs.git

### Linux

	cd clbs
	sudo ./INSTALL

### Windows
Run INSTALL.bat as administrator.


Now clbs can be used in any directory with the command `clbs`

## Usage
Building a project using clbs

	cd directory_containing_build.clbs
	clbs <target> <options>

It's recommended that plain `clbs` without targets and options builds something reasonable.

Common options

	clean    remove objects, libs and executables produced by a former build
	-jx      use x number of parallel compiler processes
	-v       print compilation commands

