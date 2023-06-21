from django.urls import path
from . import views

urlpatterns = [
    path('users/',views.show_user_list,name='technics_user_list'),
    path('users/create/',views.create_member,name='technics_create_user'),
    path('users/<int:user_id>/',views.show_user_details,name='technics_user_details'),
    path('users/<int:user_id>/edit/',views.edit_user,name='technics_edit_user'),
    path('users/<int:user_id>/password/',views.change_password,name='technics_change_password'),
    path('users/filter/',views.filter_user_list,name='techncics_filter_user_list'),
    path('sessions/',views.show_session_list,name='technics_session_list'),
    path('sessions/<int:session_id>/',views.show_session_details,name='technics_session_details'),
    path('sessions/filter/',views.filter_session_list,name='technics_filter_session_list'),
    path('sessions/create/',views.create_session,name='technics_session_create'),
    path('sessions/<int:session_id>/edit/',views.edit_session,name='technics_session_edit'),
    path('sessions/delete/<int:session_id>/',views.delete_session,name='technics_session_delete'),
    path('sessions/<int:session_id>/notes/add/',views.add_note_session,name='technics_sessionnote_add'),
    path('sessions/<int:session_id>/notes/<int:note_id>/delete/',views.delete_note_session,name='technics_sessionnote_delete'),
    path('sessions/<int:session_id>/reports/create/',views.create_report_session,name='technics_sessionreport_create'),
    path('sessions/<int:session_id>/reports/<int:report_id>/',views.show_report_session,name='technics_sessionreport_show'),
    path('sessions/<int:session_id>/reports/<int:report_id>/edit/',views.edit_report_session,name='technics_sessionreport_edit'),
    path('sessions/<int:session_id>/reports/<int:report_id>/register/',views.register_patient_report,name='technics_sessionreport_register'),
    #path('sessions/<int:session_id>/reports/<int:report_id>/generatepdf/',views.report_generate_pdf,name='technics_sessionreport_generatepdf'),
]