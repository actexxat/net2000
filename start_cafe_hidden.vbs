Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "start_silent.bat" & Chr(34), 0
Set WinScriptHost = Nothing
