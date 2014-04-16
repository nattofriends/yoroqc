import os
import shutil
import subprocess
import sys
import zipfile

from distutils.core import setup
import py2exe

sys.path.insert(0, ".")
sys.path.insert(0, "./dll")

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>TagQueryClient</description>
<dependency>
    <dependentAssembly>
      <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b" />
    </dependentAssembly>
  </dependency>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""

setup(
    options={
        'py2exe': {
            'bundle_files': 3,
            'optimize': 2,
            'dll_excludes': ["mswsock.dll", "powrprof.dll", "w9xpopen.exe", "msvcp90.dll"], # msvcp90.dll in assets.zip
        }
    },
    data_files=[
        ("", ["config.ini"]),
    ],
    windows=[{
        "script": 'yoroqc.py', 
    }],
    # zipfile=None,
)

with zipfile.ZipFile('assets.zip') as assets:
    assets.extractall("dist")
    