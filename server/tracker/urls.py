from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.HealthView.as_view()),
    path("me/", views.MeView.as_view()),
    path("tariffs/", views.TariffList.as_view()),
    path("bill/estimate/", views.BillEstimate.as_view()),
    path("meters/", views.MeterList.as_view()),
    path("meters/<int:pk>/", views.MeterDetail.as_view()),
    path("meters/<int:meter_id>/readings/", views.ReadingList.as_view()),
    path("meters/<int:meter_id>/bill/", views.MeterBill.as_view()),
    path("readings/<int:pk>/", views.ReadingDetail.as_view()),
    path("analytics/monthly/", views.MonthlyAnalytics.as_view()),
]
