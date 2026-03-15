Set objShell = CreateObject("WScript.Shell")
Set objShortcut = objShell.CreateShortcut(objShell.SpecialFolders("Desktop") & "\Controle Financeiro.lnk")
objShortcut.TargetPath = "C:\Users\illan\anaconda3\pythonw.exe"
objShortcut.Arguments = """C:\CONTROLE FINANCEIRO\controle_financeiro.py"""
objShortcut.WorkingDirectory = "C:\CONTROLE FINANCEIRO"
objShortcut.IconLocation = "C:\CONTROLE FINANCEIRO\icone.ico"
objShortcut.WindowStyle = 1
objShortcut.Description = "Controle Financeiro"
objShortcut.Save
MsgBox "Atalho criado na Area de Trabalho!" & Chr(10) & "Clique com botao direito nele e escolha 'Fixar na barra de tarefas'.", 64, "Pronto!"
