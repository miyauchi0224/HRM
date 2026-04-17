from rest_framework.permissions import IsAuthenticated


class IsNotCustomer(IsAuthenticated):
    """
    顧客ロールを排除するパーミッション。
    勤怠・給与・経費・MBO・TODO等の社内専用APIに適用する。
    顧客は IsAuthenticated を満たすが、このパーミッションは通過できない。
    """
    message = 'このページへのアクセス権限がありません。'

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and not request.user.is_customer
        )
