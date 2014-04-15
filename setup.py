import os
import shutil
import subprocess
import sys

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
            'dll_excludes': ["mswsock.dll", "powrprof.dll", "w9xpopen.exe"],
        }
    },
    data_files=[
        ("", [os.path.join("dll", file) for file in ["mfc90.dll", "mfc90u.dll", "mfcm90.dll", "mfcm90u.dll", "Microsoft.VC90.MFC.manifest"]]),
        ("", ["config.ini"]),
    ],
    windows=[{
        "script": 'yoroqc.py', 
    }],
    # zipfile=None,
)

# Fuck everything

if not os.path.exists("dist/mpc-hc"):
    shutil.copytree("mpc-hc", "dist/mpc-hc")