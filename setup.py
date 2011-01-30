from distutils.core import setup
import py2exe

setup(
	windows=[{
			'script':'aethyrHelper.py'
		}],
	options={
		"py2exe":{
		"optimize": 2,
		"excludes": ["email"],
		"bundle_files": 1,
#		"includes": ["win32com"],
		"dll_excludes": [ "mswsock.dll", "powrprof.dll" ]
		}
	}
)
