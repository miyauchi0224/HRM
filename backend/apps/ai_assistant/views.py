import anthropic
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.accounts.permissions import IsNotCustomer, IsHR


def get_client(user=None):
    """
    Anthropic クライアントを取得。
    優先順位: ユーザー個別キー → サーバー共通キー → None
    """
    api_key = ''
    if user and hasattr(user, 'anthropic_api_key') and user.anthropic_api_key:
        api_key = user.anthropic_api_key
    if not api_key:
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

        client = get_client(request.user)
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

        client = get_client(request.user)
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


class DraftMBOGoalView(APIView):
    """AIがMBO目標の文章を下書き（役職・注力分野から生成）"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        role = request.data.get('role', '')
        focus_area = request.data.get('focus_area', '')
        if not role or not focus_area:
            return Response({'error': '役職と注力分野を入力してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client(request.user)
        if not client:
            return Response({'error': 'AI機能が設定されていません（APIキーが未設定）'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prompt = f"""あなたは人事コンサルタントです。以下の情報をもとに、MBOの目標文章を3つ提案してください。
各目標は「具体的・測定可能・達成可能・関連性がある・期限がある（SMART）」原則に従って、日本語100字以内で記述してください。
番号付きリスト形式で返してください。

役職: {role}
注力分野: {focus_area}

目標案:"""

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


class HRQueryView(APIView):
    """HR向け自然言語クエリ — 社内データをAIが回答"""
    permission_classes = [IsHR]

    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'error': '質問を入力してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client(request.user)
        if not client:
            return Response({'error': 'AI機能が設定されていません（APIキーが未設定）'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 利用可能なツール定義（Claude tool_use）
        tools = [
            {
                'name': 'get_employee_list',
                'description': '社員一覧を取得する。氏名・部署・役職・在職状況を含む。',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'department': {'type': 'string', 'description': '部署名でフィルタ（省略可）'},
                    },
                    'required': [],
                },
            },
            {
                'name': 'get_attendance_summary',
                'description': '指定社員の指定月の勤怠サマリー（残業時間・出勤日数）を取得する。',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'employee_id': {'type': 'string', 'description': '社員UUID'},
                        'year_month':  {'type': 'string', 'description': 'YYYY-MM形式'},
                    },
                    'required': ['employee_id', 'year_month'],
                },
            },
            {
                'name': 'get_leave_balance',
                'description': '指定社員の有給残日数を取得する。',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'employee_id': {'type': 'string', 'description': '社員UUID'},
                    },
                    'required': ['employee_id'],
                },
            },
        ]

        try:
            messages = [{'role': 'user', 'content': question}]
            answer = self._run_agent_loop(client, tools, messages, request)
            return Response({'answer': answer})
        except Exception as e:
            return Response({'error': f'AI処理に失敗しました: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _run_agent_loop(self, client, tools, messages, request):
        """tool_use のエージェントループ（最大3ターン）"""
        from apps.employees.models import Employee
        from apps.attendance.models import AttendanceRecord
        from apps.leave.models import LeaveBalance
        from datetime import date

        for _ in range(3):
            resp = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                tools=tools,
                messages=messages,
            )

            if resp.stop_reason == 'end_turn':
                for block in resp.content:
                    if hasattr(block, 'text'):
                        return block.text
                return ''

            if resp.stop_reason != 'tool_use':
                break

            tool_results = []
            for block in resp.content:
                if block.type != 'tool_use':
                    continue
                tool_name = block.name
                tool_input = block.input

                if tool_name == 'get_employee_list':
                    qs = Employee.objects.select_related('user').all()
                    dept = tool_input.get('department')
                    if dept:
                        qs = qs.filter(department__icontains=dept)
                    result = [
                        {'id': str(e.id), 'full_name': e.full_name,
                         'department': e.department, 'position': e.position,
                         'is_active': e.retire_date is None}
                        for e in qs[:50]
                    ]

                elif tool_name == 'get_attendance_summary':
                    emp_id = tool_input.get('employee_id')
                    ym = tool_input.get('year_month', date.today().strftime('%Y-%m'))
                    year, month = ym.split('-')
                    records = list(AttendanceRecord.objects.filter(
                        employee_id=emp_id, date__year=year, date__month=month,
                    ))
                    total_work = sum(r.work_minutes for r in records)
                    total_ot   = sum(r.overtime_minutes for r in records)
                    result = {
                        'year_month': ym,
                        'work_days': len(records),
                        'total_work_hours': round(total_work / 60, 1),
                        'total_overtime_hours': round(total_ot / 60, 1),
                    }

                elif tool_name == 'get_leave_balance':
                    emp_id = tool_input.get('employee_id')
                    fiscal_year = date.today().year if date.today().month >= 4 else date.today().year - 1
                    bal = LeaveBalance.objects.filter(
                        employee_id=emp_id, fiscal_year=fiscal_year
                    ).first()
                    result = {
                        'fiscal_year': fiscal_year,
                        'remaining_days': float(bal.remaining_days) if bal else None,
                        'used_days': float(bal.used_days) if bal else None,
                    }
                else:
                    result = {'error': f'未知のツール: {tool_name}'}

                tool_results.append({
                    'type': 'tool_result',
                    'tool_use_id': block.id,
                    'content': json.dumps(result, ensure_ascii=False),
                })

            messages = messages + [
                {'role': 'assistant', 'content': resp.content},
                {'role': 'user', 'content': tool_results},
            ]

        return 'AI処理が完了しませんでした。'


class DraftIntraArticleView(APIView):
    """AIがイントラ記事の本文を下書き"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        title   = request.data.get('title', '')
        summary = request.data.get('summary', '')
        if not title:
            return Response({'error': 'タイトルを入力してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client(request.user)
        if not client:
            return Response({'error': 'AI機能が設定されていません'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prompt = f"""社内イントラネット記事の本文を日本語で作成してください。
ビジネス文書として適切な文体で、400〜800字程度にまとめてください。
タイトル: {title}
概要・ポイント: {summary}
記事本文:"""

        try:
            msg = client.messages.create(
                model='claude-haiku-4-5-20251001', max_tokens=1000,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return Response({'draft': msg.content[0].text if msg.content else ''})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DraftJobPostingView(APIView):
    """AIが採用求人票を下書き"""
    permission_classes = [IsHR]

    def post(self, request):
        job_title  = request.data.get('job_title', '')
        department = request.data.get('department', '')
        focus      = request.data.get('focus', '')
        if not job_title:
            return Response({'error': '職種名を入力してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client(request.user)
        if not client:
            return Response({'error': 'AI機能が設定されていません'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prompt = f"""以下の情報をもとに採用求人票を日本語で作成してください。
「職務内容」「必須要件」「歓迎要件」の3つのセクションに分けて記述してください。
職種: {job_title}
部署: {department}
重視する点: {focus}
求人票:"""

        try:
            msg = client.messages.create(
                model='claude-haiku-4-5-20251001', max_tokens=800,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return Response({'draft': msg.content[0].text if msg.content else ''})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DraftNextMonthIssueView(APIView):
    """AIが月報「次月の課題」を下書き"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        result = request.data.get('result', '')
        goal   = request.data.get('goal', '')

        client = get_client(request.user)
        if not client:
            return Response({'error': 'AI機能が設定されていません'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prompt = f"""以下の月報内容をもとに「次月の課題」を日本語150字程度で提案してください。
目標: {goal}
今月の結果・考察: {result}
次月の課題案:"""

        try:
            msg = client.messages.create(
                model='claude-haiku-4-5-20251001', max_tokens=300,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return Response({'draft': msg.content[0].text if msg.content else ''})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyzeExpenseReceiptView(APIView):
    """領収書画像からAIが金額・日付・内容を読み取る（OCR）"""
    permission_classes = [IsNotCustomer]

    def post(self, request):
        image_base64 = request.data.get('image_base64', '')
        media_type = request.data.get('media_type', 'image/jpeg')
        if not image_base64:
            return Response({'error': '画像データを送信してください'}, status=status.HTTP_400_BAD_REQUEST)

        client = get_client(request.user)
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
