' ====================================================================
'  Inicia a API de Integracao VTC em SEGUNDO PLANO (sem janela preta).
'  - Porta padrao: 8765
'  - Documentacao interativa: http://localhost:8765/docs
'  - Logs salvos em: api_vtc.log
'  - Para parar a API a qualquer momento: execute "PARAR_API_VTC.bat"
' ====================================================================
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
pasta = fso.GetParentFolderName(WScript.ScriptFullName)

' Executa _api_vtc_bg.bat de forma totalmente oculta (0 = janela oculta, False = nao espera terminar)
sh.Run "cmd /c """ & pasta & "\_api_vtc_bg.bat""", 0, False

' Aviso rapido na tela informando que ligou (fecha sozinho apos 4 segundos)
sh.Popup "API Barcode Academico (Porta 8765) iniciada em segundo plano." & vbCrLf & vbCrLf & _
         "- Documentacao: http://localhost:8765/docs" & vbCrLf & _
         "- Logs salvos em: api_vtc.log" & vbCrLf & vbCrLf & _
         "Para desligar a API, use 'PARAR_API_VTC.bat'.", 4, "Barcode Academico - API", 64
