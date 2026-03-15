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

strIcone = strDir & "\icone.ico"

Set objShortcut = objShell.CreateShortcut(objShell.SpecialFolders("Desktop") & "\Controle Financeiro.lnk")
objShortcut.TargetPath = strPython
objShortcut.Arguments = """" & strDir & "\main.py"""
objShortcut.WorkingDirectory = strDir
objShortcut.IconLocation = strIcone
objShortcut.WindowStyle = 1
objShortcut.Description = "Controle Financeiro"
objShortcut.Save

MsgBox "Atalho criado na Area de Trabalho!" & Chr(10) & "Clique com botao direito nele e escolha 'Fixar na barra de tarefas'.", 64, "Pronto!"
