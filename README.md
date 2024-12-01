# Docomo Mail Forwarder

## English

A simple mail forwarding service that automatically forwards emails from Docomo mail (spmode) to Gmail or other email services.

### Features
- Automatically forwards unread emails from Docomo to Gmail or other email services
- Uses IMAP protocol for both source and destination
- Includes retry mechanism for better reliability
- Runs in Docker container

### Quick Start

1. Clone this repository
2. Edit `docker-compose.yml` and replace the following values with your own:
   ```yaml
   SOURCE_EMAIL: your_docomo_email@docomo.ne.jp
   SOURCE_PASSWORD: your_docomo_password
   DEST_EMAIL: your_gmail@gmail.com
   DEST_PASSWORD: your_gmail_app_password
   ```
   
   For Gmail:
   1. Enable 2-Step Verification in your Google Account
   2. Go to Security → App Passwords
   3. Generate a new App Password for Mail

   For other email services:
   ```yaml
   DEST_IMAP_SERVER: your_email_imap_server
   DEST_IMAP_PORT: your_imap_port
   DEST_EMAIL: your_email@example.com
   DEST_PASSWORD: your_email_password
   ```

3. Run the container:
   ```bash
   docker-compose up -d
   ```

4. Check logs:
   ```bash
   docker-compose logs -f
   ```

### Requirements
- Docker
- Docker Compose

---

## 日本語

DocomoメールからGmailやその他のメールサービスへ自動転送するシンプルなメール転送サービスです。

### 特徴
- Docomoメールの未読メールを自動的にGmailやその他のメールサービスへ転送
- 送信元と送信先ともにIMAPプロトコルを使用
- 信頼性向上のための再試行メカニズム搭載
- Dockerコンテナとして実行

### クイックスタート

1. このリポジトリをクローン
2. `docker-compose.yml`を編集し、以下の値を自分のものに置き換えてください：
   ```yaml
   SOURCE_EMAIL: あなたのドコモメール@docomo.ne.jp
   SOURCE_PASSWORD: ドコモメールのパスワード
   DEST_EMAIL: あなたのGmail@gmail.com
   DEST_PASSWORD: Gmailのアプリパスワード
   ```
   
   Gmailの場合：
   1. Googleアカウントで2段階認証を有効化
   2. セキュリティ → アプリパスワード へ移動
   3. メール用の新しいアプリパスワードを生成

   その他のメールサービスの場合：
   ```yaml
   DEST_IMAP_SERVER: メールサーバーのIMAPサーバー
   DEST_IMAP_PORT: IMAPポート番号
   DEST_EMAIL: のメール@example.com
   DEST_PASSWORD: メールパスワード
   ```

3. コンテナを実行：
   ```bash
   docker-compose up -d
   ```

4. ログの確認：
   ```bash
   docker-compose logs -f
   ```

### 必要条件
- Docker
- Docker Compose 