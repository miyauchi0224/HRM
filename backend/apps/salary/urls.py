from rest_framework.routers import DefaultRouter
from .views import SalaryGradeViewSet, AllowanceViewSet, EmployeeAllowanceViewSet, PayslipViewSet

router = DefaultRouter()
router.register('grades',              SalaryGradeViewSet,       basename='salary-grade')
router.register('allowances',          AllowanceViewSet,          basename='allowance')
router.register('employee-allowances', EmployeeAllowanceViewSet,  basename='employee-allowance')
router.register('payslips',            PayslipViewSet,            basename='payslip')

urlpatterns = router.urls
