@echo off

start /min scrcpy-win64-v1.17/scrcpy.exe ^
	--always-on-top ^
	-Swt ^
	-b 1M ^
	-m 480 ^
	--window-title 'scrcpy'
	
