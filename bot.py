import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from claude_handler import ClaudeHandler

# 環境変数読み込み
load_dotenv()

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Claude ハンドラー初期化
claude = ClaudeHandler(
    api_key=os.getenv('CLAUDE_API_KEY'),
    news_api_key=os.getenv('NEWS_API_KEY')
)

# 会話履歴を保存（チャンネルごと）
conversation_history = {}

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    await bot.change_presence(activity=discord.Game(name="Claude AIと会話中"))

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return

    # コマンドを先に処理
    await bot.process_commands(message)

    # メンションされた場合のみ応答
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        # メンションを除去してメッセージを取得
        content = message.content.replace(f'<@{bot.user.id}>', '').strip()

        if not content:
            await message.channel.send("何か話しかけてください！")
            return

        # チャンネルIDで会話履歴を管理
        channel_id = message.channel.id
        if channel_id not in conversation_history:
            conversation_history[channel_id] = []

        # Typing表示
        async with message.channel.typing():
            try:
                # Claude APIで応答生成
                response = await claude.chat(
                    user_message=content,
                    conversation_history=conversation_history[channel_id]
                )

                # 会話履歴を更新
                conversation_history[channel_id].append({
                    'role': 'user',
                    'content': content
                })
                conversation_history[channel_id].append({
                    'role': 'assistant',
                    'content': response
                })

                # 履歴が長すぎる場合は古いものを削除（最新10往復まで）
                if len(conversation_history[channel_id]) > 20:
                    conversation_history[channel_id] = conversation_history[channel_id][-20:]

                # 応答を送信（2000文字制限対応）
                if len(response) > 2000:
                    # 長いメッセージは分割
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(response)

            except Exception as e:
                await message.channel.send(f"エラーが発生しました: {str(e)}")
                print(f"Error: {e}")

@bot.command(name='news', help='最新ニュースを取得します。例: !news, !news テクノロジー')
async def get_news(ctx, *, topic: str = None):
    """ニュース取得コマンド"""
    async with ctx.typing():
        try:
            if topic:
                response = await claude.get_news_summary(topic)
            else:
                response = await claude.get_news_summary("最新")

            # 応答を送信
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(response)

        except Exception as e:
            await ctx.send(f"ニュース取得エラー: {str(e)}")
            print(f"News Error: {e}")

@bot.command(name='clear', help='会話履歴をクリアします')
async def clear_history(ctx):
    """会話履歴をクリア"""
    channel_id = ctx.channel.id
    if channel_id in conversation_history:
        conversation_history[channel_id] = []
        await ctx.send("会話履歴をクリアしました！")
    else:
        await ctx.send("会話履歴はありません。")

@bot.command(name='help_claude', help='Botの使い方を表示します')
async def help_command(ctx):
    """ヘルプコマンド"""
    embed = discord.Embed(
        title="Claude AI Bot 使い方",
        description="Claude APIを使用したAI会話Bot",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="会話方法",
        value="@ボット名 メッセージ\n例: @ClaudeBot こんにちは！",
        inline=False
    )
    embed.add_field(
        name="!news [トピック]",
        value="最新ニュースを取得\n例: !news, !news AI",
        inline=False
    )
    embed.add_field(
        name="!clear",
        value="会話履歴をクリア",
        inline=False
    )
    embed.add_field(
        name="機能",
        value="- 自然な会話\n- ニュース検索と要約\n- 会話履歴の保持\n- Tool Use対応",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='ping', help='Botの応答速度を確認します')
async def ping(ctx):
    """Ping コマンド"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! レイテンシ: {latency}ms')

# Bot起動
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("エラー: DISCORD_TOKENが設定されていません")
        print(".envファイルを作成し、DISCORD_TOKENを設定してください")
    else:
        bot.run(token)
