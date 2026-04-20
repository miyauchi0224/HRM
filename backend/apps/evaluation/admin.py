from django.contrib import admin
from .models import EvaluationPeriod, EvaluationQuestion, Evaluation360, EvaluationScore
admin.site.register(EvaluationPeriod)
admin.site.register(EvaluationQuestion)
admin.site.register(Evaluation360)
admin.site.register(EvaluationScore)
