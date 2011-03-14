from distutils.core import setup

setup(
	windows=[{
			'script':'AethyrHelper.py'
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
