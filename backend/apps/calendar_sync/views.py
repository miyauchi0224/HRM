import os
import json
import jpholiday
from datetime import datetime, timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import requests
from .models import UserCalendarToken
from .serializers import UserCalendarTokenSerializer


class CalendarViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def holidays(self, request):
        """祝日情報を返す（jpholiday）"""
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year or not month:
            return Response({'error': '年月を指定してください'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            year = int(year)
            month = int(month)
            if not (1 <= month <= 12):
                return Response({'error': '月は1-12で指定してください'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': '年月は数値で指定してください'}, status=status.HTTP_400_BAD_REQUEST)

        # jpholiday.holidays() で指定年月の祝日を取得
        from datetime import date, timedelta
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # jpholiday.holidays(start_date, end_date) で該当期間の祝日を取得
        holidays_list = jpholiday.holidays(start_date, end_date)
        holidays = []
        for holiday_date, holiday_name in holidays_list:
            holidays.append({
                'date': holiday_date.isoformat(),
                'name': holiday_name,
                'type': 'holiday'
            })

        return Response({'holidays': holidays})

    @action(detail=False, methods=['get'])
    def oauth_ms_start(self, request):
        """Microsoft OAuth認証開始"""
        client_id = settings.MICROSOFT_CLIENT_ID
        if not client_id:
            return Response({'error': 'Microsoft Client ID not configured'}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = request.build_absolute_uri('/api/v1/calendar/oauth/ms/callback/')
        scope = 'Calendars.ReadWrite offline_access'
        auth_url = f'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'prompt': 'select_account'
        }
        return redirect(f'{auth_url}?{urlencode(params)}')

    @action(detail=False, methods=['get'])
    def oauth_ms_callback(self, request):
        """Microsoft OAuth コールバック"""
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Authorization code not provided'}, status=status.HTTP_400_BAD_REQUEST)

        client_id = settings.MICROSOFT_CLIENT_ID
        client_secret = settings.MICROSOFT_CLIENT_SECRET
        redirect_uri = request.build_absolute_uri('/api/v1/calendar/oauth/ms/callback/')

        # トークン交換
        token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'scope': 'Calendars.ReadWrite offline_access'
        }

        try:
            token_response = requests.post(token_url, data=token_data, timeout=10)
            token_response.raise_for_status()
            tokens = token_response.json()

            # トークンを保存
            expires_at = None
            if 'expires_in' in tokens:
                expires_at = timezone.now() + timedelta(seconds=tokens['expires_in'])

            UserCalendarToken.objects.update_or_create(
                user=request.user,
                provider=UserCalendarToken.Provider.MICROSOFT,
                defaults={
                    'access_token': tokens.get('access_token', ''),
                    'refresh_token': tokens.get('refresh_token', ''),
                    'expires_at': expires_at,
                }
            )

            return Response({'message': 'Microsoft カレンダーの同期を有効にしました'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Token exchange failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def oauth_google_start(self, request):
        """Google OAuth認証開始"""
        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            return Response({'error': 'Google Client ID not configured'}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = request.build_absolute_uri('/api/v1/calendar/oauth/google/callback/')
        scope = 'https://www.googleapis.com/auth/calendar'
        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'access_type': 'offline',
        }
        return redirect(f'{auth_url}?{urlencode(params)}')

    @action(detail=False, methods=['get'])
    def oauth_google_callback(self, request):
        """Google OAuth コールバック"""
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Authorization code not provided'}, status=status.HTTP_400_BAD_REQUEST)

        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        redirect_uri = request.build_absolute_uri('/api/v1/calendar/oauth/google/callback/')

        # トークン交換
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

        try:
            token_response = requests.post(token_url, data=token_data, timeout=10)
            token_response.raise_for_status()
            tokens = token_response.json()

            # トークンを保存
            expires_at = None
            if 'expires_in' in tokens:
                expires_at = timezone.now() + timedelta(seconds=tokens['expires_in'])

            UserCalendarToken.objects.update_or_create(
                user=request.user,
                provider=UserCalendarToken.Provider.GOOGLE,
                defaults={
                    'access_token': tokens.get('access_token', ''),
                    'refresh_token': tokens.get('refresh_token', ''),
                    'expires_at': expires_at,
                }
            )

            return Response({'message': 'Google カレンダーの同期を有効にしました'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Token exchange failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def events(self, request):
        """ユーザーのカレンダーイベントを取得（MS / Google）"""
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year or not month:
            return Response({'error': '年月を指定してください'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response({'error': '年月は数値で指定してください'}, status=status.HTTP_400_BAD_REQUEST)

        events = []

        # Microsoft カレンダーイベント取得
        try:
            ms_token = UserCalendarToken.objects.get(user=request.user, provider='ms')
            ms_events = self._get_ms_calendar_events(ms_token, year, month)
            events.extend(ms_events)
        except UserCalendarToken.DoesNotExist:
            pass
        except Exception as e:
            print(f'MS Calendar error: {e}')

        # Google カレンダーイベント取得
        try:
            google_token = UserCalendarToken.objects.get(user=request.user, provider='google')
            google_events = self._get_google_calendar_events(google_token, year, month)
            events.extend(google_events)
        except UserCalendarToken.DoesNotExist:
            pass
        except Exception as e:
            print(f'Google Calendar error: {e}')

        return Response({'events': events})

    def _get_ms_calendar_events(self, token, year, month):
        """Microsoft Graph APIでイベント取得"""
        from datetime import date
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        url = 'https://graph.microsoft.com/v1.0/me/calendarview'
        headers = {'Authorization': f'Bearer {token.access_token}'}
        params = {
            'startDateTime': start_date.isoformat() + 'T00:00:00',
            'endDateTime': end_date.isoformat() + 'T00:00:00',
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        events = []
        for item in data.get('value', []):
            events.append({
                'id': item.get('id'),
                'title': item.get('subject'),
                'start': item.get('start', {}).get('dateTime'),
                'end': item.get('end', {}).get('dateTime'),
                'provider': 'microsoft',
                'url': item.get('webLink'),
            })
        return events

    def _get_google_calendar_events(self, token, year, month):
        """Google Calendar APIでイベント取得"""
        from datetime import date
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
        headers = {'Authorization': f'Bearer {token.access_token}'}
        params = {
            'timeMin': start_date.isoformat() + 'T00:00:00Z',
            'timeMax': end_date.isoformat() + 'T00:00:00Z',
            'maxResults': 100,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        events = []
        for item in data.get('items', []):
            start = item.get('start', {})
            end = item.get('end', {})
            events.append({
                'id': item.get('id'),
                'title': item.get('summary'),
                'start': start.get('dateTime', start.get('date')),
                'end': end.get('dateTime', end.get('date')),
                'provider': 'google',
                'url': item.get('htmlLink'),
            })
        return events

    @action(detail=False, methods=['post'])
    def oauth_revoke(self, request):
        """OAuth連携を解除"""
        provider = request.data.get('provider')  # 'ms' or 'google'
        if not provider:
            return Response({'error': 'provider を指定してください'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = UserCalendarToken.objects.get(user=request.user, provider=provider)
            token.delete()
            return Response({'message': f'{dict(UserCalendarToken.Provider.choices).get(provider, provider)} の連携を解除しました'})
        except UserCalendarToken.DoesNotExist:
            return Response({'error': '連携情報が見つかりません'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def tokens(self, request):
        """ユーザーの保存済みトークン一覧（プロバイダーのみ）"""
        tokens = UserCalendarToken.objects.filter(user=request.user, is_deleted=False).values_list('provider', flat=True)
        return Response({'providers': list(tokens)})

    @action(detail=False, methods=['post'])
    def create_event(self, request):
        """カレンダーに予定を追加"""
        title = request.data.get('title')
        date_str = request.data.get('date')
        provider = request.data.get('provider')  # 'ms' or 'google'

        if not title or not date_str or not provider:
            return Response({'error': '必須フィールドが不足しています'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = UserCalendarToken.objects.get(user=request.user, provider=provider)
        except UserCalendarToken.DoesNotExist:
            return Response({'error': f'カレンダーが同期されていません'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if provider == 'ms':
                event_id = self._create_ms_calendar_event(token, title, date_str)
            else:  # google
                event_id = self._create_google_calendar_event(token, title, date_str)

            return Response({'message': '予定を追加しました', 'event_id': event_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'予定の追加に失敗しました: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def _create_ms_calendar_event(self, token, title, date_str):
        """Microsoft Graphで予定を追加"""
        from datetime import datetime, time
        event_date = datetime.fromisoformat(date_str).date()
        start_time = datetime.combine(event_date, time(9, 0))
        end_time = datetime.combine(event_date, time(10, 0))

        url = 'https://graph.microsoft.com/v1.0/me/events'
        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'subject': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Tokyo'
            }
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json().get('id')

    def _create_google_calendar_event(self, token, title, date_str):
        """Google Calendarで予定を追加"""
        from datetime import datetime, time
        event_date = datetime.fromisoformat(date_str).date()
        start_time = datetime.combine(event_date, time(9, 0))
        end_time = datetime.combine(event_date, time(10, 0))

        url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Tokyo'
            }
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json().get('id')
