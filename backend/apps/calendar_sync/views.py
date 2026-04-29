import os
import json
import holidays
import csv
from datetime import datetime, timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import requests
from .models import UserCalendarToken, CalendarEvent
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

        # holidays ライブラリで日本の祝日を取得
        from datetime import date
        jp_holidays = holidays.Japan(years=year)

        holidays_list = []
        for holiday_date, holiday_name in sorted(jp_holidays.items()):
            # 指定月の祝日のみフィルタ
            if holiday_date.month == month and holiday_date.year == year:
                holidays_list.append({
                    'date': holiday_date.isoformat(),
                    'name': holiday_name,
                    'type': 'holiday'
                })

        return Response({'holidays': holidays_list})

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
        """ユーザーのカレンダーイベントを取得（DB + MS / Google）"""
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

        # DB から保存済みイベント取得
        db_events = CalendarEvent.objects.filter(
            user=request.user,
            is_deleted=False,
            start_datetime__year=year,
            start_datetime__month=month
        ).order_by('start_datetime')

        for event in db_events:
            # provider を統一フォーマットに変換
            provider_map = {
                'ms': 'microsoft',
                'google': 'google',
                'local': 'local',
            }
            events.append({
                'id': str(event.id),
                'title': event.title,
                'start': event.start_datetime.isoformat(),
                'end': event.end_datetime.isoformat(),
                'provider': provider_map.get(event.provider, 'local'),
                'url': event.url,
            })

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
        """カレンダーに予定を追加（DB保存 + 外部カレンダー同期）"""
        title = request.data.get('title')
        date_str = request.data.get('date')
        provider = request.data.get('provider')  # 'ms', 'google', 'local'
        start_time_str = request.data.get('start_time', '09:00')  # デフォルト 9:00
        end_time_str = request.data.get('end_time', '10:00')  # デフォルト 10:00

        if not title or not date_str or not provider:
            return Response({'error': '必須フィールドが不足しています'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from datetime import datetime, time
            event_date = datetime.fromisoformat(date_str).date()

            # 時刻の解析
            try:
                start_parts = start_time_str.split(':')
                end_parts = end_time_str.split(':')
                start_time = datetime.combine(
                    event_date,
                    time(int(start_parts[0]), int(start_parts[1]) if len(start_parts) > 1 else 0)
                )
                end_time = datetime.combine(
                    event_date,
                    time(int(end_parts[0]), int(end_parts[1]) if len(end_parts) > 1 else 0)
                )
            except (ValueError, IndexError):
                start_time = datetime.combine(event_date, time(9, 0))
                end_time = datetime.combine(event_date, time(10, 0))

            # DB に保存
            db_event = CalendarEvent.objects.create(
                user=request.user,
                title=title,
                start_datetime=start_time,
                end_datetime=end_time,
                provider=provider
            )

            external_id = None

            # 外部カレンダーに同期（オプション）
            if provider == 'ms':
                try:
                    token = UserCalendarToken.objects.get(user=request.user, provider='ms')
                    external_id = self._create_ms_calendar_event(token, title, date_str)
                    db_event.external_id = external_id
                    db_event.save()
                except UserCalendarToken.DoesNotExist:
                    pass  # MS 同期未設定の場合はスキップ
            elif provider == 'google':
                try:
                    token = UserCalendarToken.objects.get(user=request.user, provider='google')
                    external_id = self._create_google_calendar_event(token, title, date_str)
                    db_event.external_id = external_id
                    db_event.save()
                except UserCalendarToken.DoesNotExist:
                    pass  # Google 同期未設定の場合はスキップ

            return Response(
                {'message': '予定を追加しました', 'event_id': str(db_event.id)},
                status=status.HTTP_201_CREATED
            )
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

    @action(detail=False, methods=['post'])
    def update_event(self, request):
        """カレンダーの予定を更新（DB + 外部カレンダー）"""
        event_id = request.data.get('event_id')
        provider = request.data.get('provider')  # 'ms', 'google', or 'local'
        title = request.data.get('title')
        start = request.data.get('start')
        end = request.data.get('end')

        if not event_id or not provider:
            return Response({'error': '必須フィールドが不足しています'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # DB の CalendarEvent を更新
            try:
                event = CalendarEvent.objects.get(id=event_id, user=request.user)
                if title:
                    event.title = title
                if start:
                    event.start_datetime = start
                if end:
                    event.end_datetime = end
                event.save()
            except CalendarEvent.DoesNotExist:
                return Response({'error': 'イベントが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

            # 外部カレンダーがあれば同期
            if provider in ['ms', 'google'] and event.external_id:
                try:
                    token = UserCalendarToken.objects.get(user=request.user, provider=provider)
                    if provider == 'ms':
                        self._update_ms_calendar_event(token, event.external_id, title, start, end)
                    else:  # google
                        self._update_google_calendar_event(token, event.external_id, title, start, end)
                except UserCalendarToken.DoesNotExist:
                    pass  # 外部同期未設定でも DB 更新は成功

            return Response({'message': '予定を更新しました'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'予定の更新に失敗しました: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def _update_ms_calendar_event(self, token, event_id, title, start, end):
        """Microsoft Graphで予定を更新"""
        url = f'https://graph.microsoft.com/v1.0/me/events/{event_id}'
        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json'
        }
        data = {}
        if title:
            data['subject'] = title
        if start:
            data['start'] = {
                'dateTime': start,
                'timeZone': 'Asia/Tokyo'
            }
        if end:
            data['end'] = {
                'dateTime': end,
                'timeZone': 'Asia/Tokyo'
            }

        response = requests.patch(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()

    def _update_google_calendar_event(self, token, event_id, title, start, end):
        """Google Calendarで予定を更新"""
        url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'
        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json'
        }
        data = {}
        if title:
            data['summary'] = title
        if start:
            data['start'] = {
                'dateTime': start,
                'timeZone': 'Asia/Tokyo'
            }
        if end:
            data['end'] = {
                'dateTime': end,
                'timeZone': 'Asia/Tokyo'
            }

        response = requests.patch(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()

    @action(detail=False, methods=['post'])
    def delete_event(self, request):
        """カレンダーの予定を削除（DB + 外部カレンダー）"""
        event_id = request.data.get('event_id')
        provider = request.data.get('provider')  # 'ms', 'google', or 'local'

        if not event_id or not provider:
            return Response({'error': '必須フィールドが不足しています'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # DB の CalendarEvent を取得
            try:
                event = CalendarEvent.objects.get(id=event_id, user=request.user)
            except CalendarEvent.DoesNotExist:
                return Response({'error': 'イベントが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

            # 外部カレンダーがあれば同期
            if provider in ['ms', 'google'] and event.external_id:
                try:
                    token = UserCalendarToken.objects.get(user=request.user, provider=provider)
                    if provider == 'ms':
                        self._delete_ms_calendar_event(token, event.external_id)
                    else:  # google
                        self._delete_google_calendar_event(token, event.external_id)
                except UserCalendarToken.DoesNotExist:
                    pass  # 外部同期未設定でも DB 削除は実行

            # DB から削除（soft delete）
            event.delete()

            return Response({'message': '予定を削除しました'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'予定の削除に失敗しました: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def _delete_ms_calendar_event(self, token, event_id):
        """Microsoft Graphで予定を削除"""
        url = f'https://graph.microsoft.com/v1.0/me/events/{event_id}'
        headers = {'Authorization': f'Bearer {token.access_token}'}
        response = requests.delete(url, headers=headers, timeout=10)
        response.raise_for_status()

    def _delete_google_calendar_event(self, token, event_id):
        """Google Calendarで予定を削除"""
        url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'
        headers = {'Authorization': f'Bearer {token.access_token}'}
        response = requests.delete(url, headers=headers, timeout=10)
        response.raise_for_status()

    @action(detail=False, methods=['get'])
    def export_events(self, request):
        """カレンダーイベントをエクスポート（CSV）"""
        format_type = request.query_params.get('format', 'csv')  # csv または ics
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        # ユーザーのイベントを取得
        events = CalendarEvent.objects.filter(user=request.user, is_deleted=False)

        if year and month:
            try:
                year = int(year)
                month = int(month)
                events = events.filter(start_datetime__year=year, start_datetime__month=month)
            except ValueError:
                pass

        events = events.order_by('start_datetime')

        if format_type == 'ics':
            return self._export_ics(events)
        else:  # csv
            return self._export_csv(events)

    def _export_csv(self, events):
        """CSV形式でエクスポート（UTF-8 BOM付き）"""
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="calendar_events.csv"'
        response.write('﻿')  # UTF-8 BOM

        writer = csv.writer(response)
        writer.writerow(['タイトル', '開始日時', '終了日時', 'プロバイダー', '作成日'])

        for event in events:
            writer.writerow([
                event.title,
                event.start_datetime.strftime('%Y-%m-%d %H:%M'),
                event.end_datetime.strftime('%Y-%m-%d %H:%M'),
                event.get_provider_display(),
                event.created_at.strftime('%Y-%m-%d'),
            ])

        return response

    def _export_ics(self, events):
        """ICS形式でエクスポート"""
        response = HttpResponse(content_type='text/calendar; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="calendar_events.ics"'

        ics_content = 'BEGIN:VCALENDAR\r\n'
        ics_content += 'VERSION:2.0\r\n'
        ics_content += 'PRODID:-//HRM Calendar//EN\r\n'
        ics_content += 'CALSCALE:GREGORIAN\r\n'

        for event in events:
            ics_content += 'BEGIN:VEVENT\r\n'
            ics_content += f'UID:{event.id}@hrm\r\n'
            ics_content += f'SUMMARY:{event.title}\r\n'
            ics_content += f'DTSTART:{event.start_datetime.strftime("%Y%m%dT%H%M%S")}\r\n'
            ics_content += f'DTEND:{event.end_datetime.strftime("%Y%m%dT%H%M%S")}\r\n'
            ics_content += f'DTSTAMP:{event.created_at.strftime("%Y%m%dT%H%M%SZ")}\r\n'
            ics_content += f'CREATED:{event.created_at.strftime("%Y%m%dT%H%M%SZ")}\r\n'
            ics_content += f'LAST-MODIFIED:{event.updated_at.strftime("%Y%m%dT%H%M%SZ")}\r\n'
            ics_content += 'END:VEVENT\r\n'

        ics_content += 'END:VCALENDAR\r\n'
        response.write(ics_content)
        return response
