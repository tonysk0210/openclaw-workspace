# MEMORY.md — Clawton 長期記憶

## 工具與能力

- **寄 Email（SMTP，已設定可用）** — 2026-05-31 建立
  - 腳本：`scripts/send_mail.py`（Python `smtplib`，SSL 465）
  - 寄件帳號：`openclaw0210@gmail.com`（助理專用 Gmail）
  - App 密碼存在 macOS Keychain：service `clawton-gmail-smtp`，account = 寄件信箱（不落地明文）
  - 用法：`python3 scripts/send_mail.py --to <addr> --subject "..." --body-file <f> [--attach <f>...]`
  - 背景：本機 Mail.app 的 Google 帳號常被停用、不穩；改走 SMTP 最可靠且可自動化。

## Tony 的信箱

- 工作：`anthony.shangkuan@hnsquare.com.tw`（USER.md 登記）
- 個人 Gmail：`anthonyshangkuan@gmail.com`
- 助理專用：`openclaw0210@gmail.com`（用於收 Clawton 寄出的自動摘要等）
- 注意：`tonyshangkuan@gmail.com`（少 an）疑似筆誤，勿用。
