"""distutils.command

Package containing implementation of all the standard Distutils
commands."""

# This module should be kept compatible with Python 2.1.

__revision__ = "$Id: __init__.py 71426 2009-04-10 00:26:09Z richard.tew $"

__all__ = ['build',
           'build_py',
           'build_ext',
           'build_clib',
           'build_scripts',
           'clean',
           'install',
           'install_lib',
           'install_headers',
           'install_scripts',
           'install_data',
           'sdist',
           'register',
           'bdist',
           'bdist_dumb',
           'bdist_rpm',
           'bdist_wininst',
           'upload',

           # These two are reserved for future use:
           #'bdist_sdux',
           #'bdist_pkgtool',
           # Note:
           # bdist_packager is not included because it only provides
           # an abstract base class
          ]
