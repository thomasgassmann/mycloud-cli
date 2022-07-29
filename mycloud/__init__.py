# pylint: disable=missing-docstring
__author__ = 'Thomas Gassmann'
__email__ = 'thomas@gassmann.dev'
version_string = '#{GitVersion}#'
__version__ = 'dev' if 'GitVersion' in version_string else version_string
