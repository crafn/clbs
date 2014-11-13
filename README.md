#clbs

Build system for Project Clover written in Python 2.7

## Installation
1.  Install [Python 2.7](https://www.python.org/download/releases/2.7/) and [git](http://git-scm.com/)
    - on Windows, remember to add Python directory to your `PATH` environment variable
2.  Obtain this repository by `git clone https://github.com/crafn/clbs.git` or by downloading the [zip](https://github.com/crafn/clbs/archive/master.zip)
3.  Run `INSTALL` on Linux or `INSTALL.bat` on Windows as administrator

The command `clbs` works now in any directory.

## Usage
Building a project using clbs

	cd directory_containing_build.clbs
	clbs <target> <options>

It's recommended that plain `clbs` without targets and options builds something reasonable.

Common options

	clean    remove objects, libs and executables produced by a former build
	-jx      use x number of parallel compiler processes
	-v       print compilation commands
