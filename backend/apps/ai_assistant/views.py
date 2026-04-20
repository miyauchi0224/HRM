import anthropic
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.accounts.permissions import IsNotCustomer


def get_client():
    """Anthropic クライアントを取得（API キーが設定されていない場合は None）"""
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


class DraftDailyReportView(APIView):
    """AIが日報の文章を下書きする"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        bullet_points = request.data.get('bullet_points', '')
        if not bullet_points:
            return Response({'error': '箇条書きを入力してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client()
        if not client:
            return Response({'error': 'AI機能が設定されていません（APIキーが未設定）'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prompt = f"""以下の箇条書きメモをもとに、ビジネス日報の文章を日本語で作成してください。
200〜400字程度で、「本日の作業内容」「成果・気づき」「明日の予定」の3つのパートに分けて書いてください。

メモ:
{bullet_points}

日報:"""

        try:
            message = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=800,
                messages=[{'role': 'user', 'content': prompt}],
            )
            draft = message.content[0].text if message.content else ''
            return Response({'draft': draft})
        except Exception as e:
            return Response({'error': f'AI生成に失敗しました: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DraftMBOReportView(APIView):
    """MBO月報の文章をAIが下書き"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        goal = request.data.get('goal', '')
        actions = request.data.get('actions', '')
        if not goal:
            return Response({'error': '目標を入力してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client()
        if not client:
            return Response({'error': 'AI機能が設定されていません（APIキーが未設定）'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prompt = f"""以下の情報をもとに、MBO月報の「行動内容と結果・結論」を日本語300字程度で作成してください。

目標: {goal}
今月の取り組み内容: {actions}

月報文章:"""

        try:
            message = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=600,
                messages=[{'role': 'user', 'content': prompt}],
            )
            draft = message.content[0].text if message.content else ''
            return Response({'draft': draft})
        except Exception as e:
            return Response({'error': f'AI生成に失敗しました: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyzeExpenseReceiptView(APIView):
    """領収書画像からAIが金額・日付・内容を読み取る（OCR）"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        image_base64 = request.data.get('image_base64', '')
        media_type = request.data.get('media_type', 'image/jpeg')
        if not image_base64:
            return Response({'error': '画像データを送信してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client()
        if not client:
            return Response({'error': 'AI機能が設定されていません（APIキーが未設定）'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            message = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=400,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': media_type,
                                'data': image_base64,
                            },
                        },
                        {
                            'type': 'text',
                            'text': '領収書の画像から以下をJSON形式で抽出してください。キーはamount（金額・数値）、date（日付・YYYY-MM-DD形式）、description（内容・店舗名や品目）。不明な場合はnullにしてください。JSONのみ返してください。',
                        },
                    ],
                }],
            )
            import json
            text = message.content[0].text if message.content else '{}'
            try:
                data = json.loads(text.strip())
            except json.JSONDecodeError:
                data = {'raw': text}
            return Response(data)
        except Exception as e:
            return Response({'error': f'AI解析に失敗しました: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
