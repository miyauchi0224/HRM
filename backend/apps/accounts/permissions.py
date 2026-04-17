from rest_framework.permissions import IsAuthenticated


class IsNotCustomer(IsAuthenticated):
    """
    顧客ロールを排除するパーミッション。
    勤怠・給与・経費・MBO・TODO等の社内専用APIに適用する。
    """
    message = 'このページへのアクセス権限がありません。'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_customer


class IsSupervisor(IsAuthenticated):
    """
    上司以上（supervisor / manager / hr / accounting / admin）のみ許可。
    部下の勤怠・休暇・MBOの承認操作に使用する。
    """
    message = '上司以上の権限が必要です。'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_supervisor


class IsHR(IsAuthenticated):
    """
    人事以上（hr / admin）のみ許可。
    社員マスタ・給与等級・手当の編集操作に使用する。
    """
    message = '人事担当以上の権限が必要です。'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_hr


class IsAccounting(IsAuthenticated):
    """
    経理以上（accounting / hr / admin）のみ許可。
    給与計算・勘定科目管理・経費承認操作に使用する。
    """
    message = '経理以上の権限が必要です。'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_accounting
