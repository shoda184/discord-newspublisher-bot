# Discord Claude AI Bot

Claude APIを使用したインテリジェントなDiscord Bot。自然な会話とニュース検索機能を搭載。

## 機能

- Claude APIによる高品質な会話
- 自動ニュース検索（Tool Use対応）
- 会話履歴の保持（チャンネルごと）
- ニュース要約機能
- 日本語完全対応

## 必要なもの

1. **Python 3.8以上**
2. **Discord Bot Token** - [Discord Developer Portal](https://discord.com/developers/applications)
3. **Claude API Key** - [Anthropic Console](https://console.anthropic.com/)
4. **NewsAPI Key（オプション）** - [NewsAPI](https://newsapi.org/) 無料プランあり

## セットアップ

### 1. 依存関係のインストール

```bash
cd Discord-newspush
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーして編集：

```bash
cp .env.example .env
```

`.env` ファイルを編集：

```env
DISCORD_TOKEN=あなたのDiscordBotトークン
CLAUDE_API_KEY=あなたのClaudeAPIキー
NEWS_API_KEY=あなたのNewsAPIキー（オプション）
```

### 3. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリック
3. アプリ名を入力（例: Claude Bot）
4. 左メニューから「Bot」を選択
5. 「Add Bot」をクリック
6. 「TOKEN」セクションで「Reset Token」をクリックしてトークンをコピー
7. 「Privileged Gateway Intents」で以下を有効化：
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT

### 4. Botをサーバーに招待

1. 左メニューから「OAuth2」→「URL Generator」
2. 「SCOPES」で`bot`を選択
3. 「BOT PERMISSIONS」で以下を選択：
   - Send Messages
   - Read Messages/View Channels
   - Read Message History
   - Use Slash Commands
4. 生成されたURLをブラウザで開いてサーバーに招待

### 5. Claude API Keyの取得

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. ログイン（Proプランとは別）
3. 「API Keys」で新しいキーを作成
4. 初回は$5のクレジット付与

### 6. NewsAPI Keyの取得（オプション）

1. [NewsAPI](https://newsapi.org/register) で登録
2. 無料プラン: 1日100リクエストまで
3. APIキーをコピー

## 起動方法

```bash
python bot.py
```

起動成功すると以下のように表示されます：

```
ClaudeBot#1234 としてログインしました！
Bot ID: 123456789012345678
------
```

## 使い方

### 基本的な会話

Botをメンションして話しかけます：

```
@ClaudeBot こんにちは！
@ClaudeBot Pythonでリストをソートする方法を教えて
@ClaudeBot 面白いジョークを教えて
```

### コマンド

#### ニュース検索
```
!news
!news テクノロジー
!news AI
!news スポーツ
```

#### 会話履歴クリア
```
!clear
```

#### ヘルプ表示
```
!help_claude
```

#### 接続確認
```
!ping
```

## Tool Use機能

Claudeは会話の文脈から自動的にニュース検索が必要かを判断します：

**例:**
```
ユーザー: 最近のAI業界のニュースについて教えて
Claude: （自動的にニュース検索ツールを実行 → 結果を要約して返答）
```

この機能により、明示的に`!news`コマンドを使わなくても、自然な会話の中でニュースを取得できます。

## ファイル構成

```
Discord-newspush/
├── bot.py                # Discord Botメイン
├── claude_handler.py     # Claude API連携
├── requirements.txt      # 依存関係
├── .env                  # 環境変数（作成必要）
├── .env.example          # 環境変数のテンプレート
├── .gitignore           # Git無視ファイル
└── README.md            # このファイル
```

## トラブルシューティング

### Botが応答しない

1. `.env`ファイルが正しく設定されているか確認
2. Discord Developer Portalで「MESSAGE CONTENT INTENT」が有効か確認
3. Botがサーバーに参加しているか確認

### Claude APIエラー

1. API Keyが正しいか確認
2. APIクレジットが残っているか確認（[Console](https://console.anthropic.com/)で確認）
3. レート制限に達していないか確認

### NewsAPIエラー

1. API Keyが正しいか確認
2. 無料プランの制限（100リクエスト/日）を超えていないか確認
3. NewsAPIが必須でない場合は`.env`から`NEWS_API_KEY`を削除可能

## コスト目安

### Claude API（従量課金）
- Claude 3.5 Sonnet: 入力 $3/MTok, 出力 $15/MTok
- 1メッセージあたり約$0.01-0.05
- 100メッセージで約$1-5

### NewsAPI
- 無料プラン: 1日100リクエスト
- 有料プラン: $449/月〜（通常不要）

## セキュリティ注意

- `.env`ファイルは絶対にGitにコミットしない
- APIキーは誰にも共有しない
- 公開リポジトリに置く場合は`.gitignore`を確認

## ライセンス

MIT License

## サポート

問題が発生した場合は、Issueを作成してください。
