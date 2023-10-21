call doc\make.bat clean
call doc\make.bat html
pause
start doc\_build\html\index.html
pause
call doc\make.bat clean
call doc\make.bat latexpdf
pause
start doc\_build\latex\pyzx.pdf
