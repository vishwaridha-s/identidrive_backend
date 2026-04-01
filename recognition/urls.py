from django.urls import path
from . import views

urlpatterns = [
    path('upload-video/', views.upload_video, name='upload_video'),
    path('detect-plates/', views.detect_plates_view, name='detect_plates'),
    path('recognize-plate/', views.recognize_plate_view, name='recognize_plate'),
    path('capture-frame/', views.capture_frame, name='capture_frame'),
    path('get-predictions/', views.get_predictions, name='get_predictions'),
]