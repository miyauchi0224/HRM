from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    全 ViewSet 共通のページネーション設定。
    - デフォルト: 20件/ページ
    - ?page_size=N で最大100件まで変更可
    - ?page=N でページ切替
    レスポンス形式:
      { count, next, previous, results: [...] }
    """
    page_size            = 20
    page_size_query_param = 'page_size'
    max_page_size        = 100
