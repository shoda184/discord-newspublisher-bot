import anthropic
import requests
import json
from datetime import datetime

class ClaudeHandler:
    """Claude APIとのやり取りを管理するクラス"""

    def __init__(self, api_key: str, news_api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.news_api_key = news_api_key
        self.model = "claude-sonnet-4-20250514"  # 安定版モデル
        # 注: 利用可能なモデル
        # - claude-3-5-sonnet-20240620 (推奨)
        # - claude-3-opus-20240229 (最高品質)
        # - claude-3-sonnet-20240229 (バランス型)
        # - claude-3-haiku-20240307 (高速・安価)

        # Tool定義（Claude Tool Use）
        self.tools = [
            {
                "name": "search_news",
                "description": "最新のニュース記事を検索します。キーワードやトピックを指定して、関連するニュース記事を取得できます。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索キーワードまたはトピック（例: テクノロジー、スポーツ、政治）"
                        },
                        "language": {
                            "type": "string",
                            "description": "言語コード（ja=日本語、en=英語）",
                            "default": "ja"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_top_headlines",
                "description": "指定したカテゴリまたは国のトップニュースを取得します。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "ニュースカテゴリ（business, entertainment, general, health, science, sports, technology）",
                            "default": "general"
                        },
                        "country": {
                            "type": "string",
                            "description": "国コード（jp=日本、us=アメリカ）",
                            "default": "jp"
                        }
                    },
                    "required": []
                }
            }
        ]

    async def chat(self, user_message: str, conversation_history: list = None):
        """
        Claudeと会話する
        Tool Useに対応し、必要に応じてニュース検索を実行
        """
        if conversation_history is None:
            conversation_history = []

        # 新しいメッセージを追加
        messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]

        # システムプロンプト
        system_prompt = """あなたはDiscord上で動作するニュース配信AIアシスタントです。

【重要】ツール使用ルール：
- ユーザーが「ニュース」「最新」「今日」「最近」などのキーワードを含む質問をした場合、**必ず**search_newsまたはget_top_headlinesツールを使用してください
- 同様にユーザーのプロンプトに「!News」という文字列が含まれる場合、**必ず**search_newsまたはget_top_headlinesツールを使用してください
- 時事的な話題、企業の動向、技術トレンドについて聞かれた場合も、**必ず**ツールを使用して最新情報を取得してください
- ツールを使用せずに自分の知識だけで回答することは厳禁です

【絶対厳守】ニュース記事のURL表示ルール：
ツールから取得した各記事について、以下の形式で**必ず全項目を表示**してください：

1. **[記事タイトル]**
   📝 要約: [記事の要約（200~250字程度）]
   📚 背景: [記事内容を理解するための背景知識（130~170文字）]
   💭 今後: [記事内容を受けて今後どうなるかの考察（130~170文字）]
   🔗 URL: [記事のURL - これは絶対に省略禁止]
   📅 日時: [publishedAt]
   📰 出典: [source name]

複数記事がある場合も同様に、**全ての記事のURLを必ず表示**してください。なお、一度の応答に含まれる記事数は3つまでとします。
URLを省略したり、「出典: 〇〇」だけで済ませることは絶対に禁止です。
ユーザーが記事にアクセスできるよう、完全なURLを必ず含めてください。
各項目の間には改行を2つ入れてください。ただし、日時と出典の間は改行1つで構いません。
ニュース記事とニュース記事の間には改行を3つ入れてください。


"""
# 正しい例：
# 1. **オラクルへの警戒広がる、巨額のAI投資でデフォルト・スワップが高騰**
#    📝 要約: オラクルが人工知能（AI）関連投資に数十億ドルを投じる中で...
#    🔗 URL: https://www.bloomberg.co.jp/news/articles/2025-10-30/example
#    📅 日時: 2025年10月30日
#    📰 出典: Bloomberg.co.jp

# 間違った例（これは絶対NG）：
# ❌ オラクルへの警戒広がる、巨額のAI投資でデフォルト・スワップが高騰
#    出典: Bloomberg.co.jp
#    日時: 2025年10月30日
#    要約: オラクルが...
#    （URLがない！これは禁止！）

        try:
            # Claude APIを呼び出し（Tool Use対応）
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Tool Useのチェック
            print(f"[DEBUG] Response stop_reason: {response.stop_reason}")
            print(f"[DEBUG] Response content blocks: {len(response.content)}")

            while response.stop_reason == "tool_use":
                # Toolの実行
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        print(f"[TOOL USE] Tool実行: {tool_name}, Input: {tool_input}")

                        # Tool実行
                        if tool_name == "search_news":
                            result = self._search_news(
                                query=tool_input.get("query"),
                                language=tool_input.get("language", "ja")
                            )
                        elif tool_name == "get_top_headlines":
                            result = self._get_top_headlines(
                                category=tool_input.get("category", "general"),
                                country=tool_input.get("country", "jp")
                            )
                        else:
                            result = {"error": "Unknown tool"}

                        print(f"[TOOL RESULT] {tool_name} returned {len(result.get('articles', []))} articles")
                        if result.get('articles'):
                            for i, article in enumerate(result['articles'][:2]):
                                print(f"  Article {i+1}: {article.get('title', 'No title')[:50]}...")
                                print(f"  URL: {article.get('url', 'No URL')}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })

                # Tool結果を含めて再度APIを呼び出し
                # response.contentをリストとして追加（Claude APIの仕様に準拠）
                assistant_content = []
                for block in response.content:
                    if hasattr(block, 'type'):
                        if block.type == "text" and hasattr(block, 'text'):
                            assistant_content.append({"type": "text", "text": block.text})
                        elif block.type == "tool_use":
                            assistant_content.append({
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input
                            })

                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})

                # 2回目の呼び出しでURL表示を強制
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt + "\n\n【再確認】今、ツール実行結果を受け取りました。各記事の'url'フィールドを必ず🔗 URL: の形式で表示してください。URLがない記事は絶対にありません。",
                    tools=self.tools,
                    messages=messages
                )

            # 最終的な応答テキストを取得
            response_text = ""
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    response_text += content_block.text

            print(f"[FINAL RESPONSE] Length: {len(response_text)} chars")
            print(f"[FINAL RESPONSE] Contains URL: {'http' in response_text}")

            return response_text

        except Exception as e:
            print(f"Claude API Error: {e}")
            return f"申し訳ございません。エラーが発生しました: {str(e)}"

    async def get_news_summary(self, topic: str):
        """
        指定されたトピックのニュースを取得して要約
        必須要件：
- 記事のタイトルとURLを必ず含めてください
- URLは必ず表示してください（例：https://example.com/article）
- 複数のニュースがある場合は、各記事のタイトルとURLをリスト形式で表示してください
- ニュースの要約と共に、ユーザーが元記事にアクセスできるようにしてください

フォーマット例：
📰 **記事タイトル**
要約内容...
🔗 https://example.com/article
背景知識...
今後の考察...

複数記事の場合：
1. **記事1のタイトル**
   要約...
   🔗 https://example.com/article1
   背景知識...
   今後の考察...

2. **記事2のタイトル**
   要約...
   🔗 https://example.com/article2
   背景知識...
   今後の考察...
"""
        user_message = f"{topic}に関する最新ニュースを教えてください。"
        return await self.chat(user_message)

    def _search_news(self, query: str, language: str = "ja"):
        """
        NewsAPIでニュース検索
        日本語で見つからない場合は英語でも試す
        """
        if not self.news_api_key:
            return {"error": "NewsAPI key is not configured"}

        url = "https://newsapi.org/v2/everything"

        # まず指定言語で検索
        params = {
            "q": query,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": self.news_api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles = []
                for article in data.get("articles", [])[:5]:
                    articles.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "publishedAt": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name")
                    })

                # 結果が0件で日本語検索だった場合、英語で再試行
                if len(articles) == 0 and language == "ja":
                    print(f"日本語ニュースが見つかりませんでした。英語で再検索します: {query}")
                    params["language"] = "en"
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    if data.get("status") == "ok":
                        for article in data.get("articles", [])[:5]:
                            articles.append({
                                "title": article.get("title"),
                                "description": article.get("description"),
                                "url": article.get("url"),
                                "publishedAt": article.get("publishedAt"),
                                "source": article.get("source", {}).get("name")
                            })

                return {"articles": articles, "totalResults": data.get("totalResults", 0)}
            else:
                return {"error": data.get("message", "Unknown error")}

        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    def _get_top_headlines(self, category: str = "general", country: str = "jp"):
        """
        NewsAPIでトップニュース取得
        """
        if not self.news_api_key:
            return {"error": "NewsAPI key is not configured"}

        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": country,
            "category": category,
            "pageSize": 5,
            "apiKey": self.news_api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles = []
                for article in data.get("articles", [])[:5]:
                    articles.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "publishedAt": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name")
                    })
                return {"articles": articles, "totalResults": data.get("totalResults", 0)}
            else:
                return {"error": data.get("message", "Unknown error")}

        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
