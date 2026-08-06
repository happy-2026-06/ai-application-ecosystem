' AI 项目集群 — 桌面一键启动 (Docker 版)
' 双击即启动, 最小化窗口, 无需任何交互

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\35220\OneDrive\Desktop\AI应用项目"
WshShell.Run "docker compose up -d", 7, True

' 等几秒让容器启动
WScript.Sleep 8000

' 打开三个项目页面
WshShell.Run "http://127.0.0.1:3001"
WScript.Sleep 500
WshShell.Run "http://127.0.0.1:3002"
WScript.Sleep 500
WshShell.Run "http://127.0.0.1:3000"

Set WshShell = Nothing
