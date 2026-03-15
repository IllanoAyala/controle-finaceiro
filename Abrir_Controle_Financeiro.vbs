Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

strPython = ""
Dim arrPaths(5)
arrPaths(0) = objShell.ExpandEnvironmentStrings("%USERPROFILE%\anaconda3\pythonw.exe")
arrPaths(1) = objShell.ExpandEnvironmentStrings("%USERPROFILE%\miniconda3\pythonw.exe")
arrPaths(2) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe")
arrPaths(3) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe")
arrPaths(4) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe")
arrPaths(5) = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Microsoft\WindowsApps\pythonw.exe")

Dim i
For i = 0 To 5
    If objFSO.FileExists(arrPaths(i)) Then
        strPython = arrPaths(i)
        Exit For
    End If
Next

If strPython = "" Then
    MsgBox "Python nao encontrado." & Chr(10) & "Instale o Python 3.8+ e tente novamente.", 16, "Erro"
    WScript.Quit
End If

objShell.Run """" & strPython & """ """ & strDir & "\main.py""", 0, False
