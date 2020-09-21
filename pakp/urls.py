from ckeditor_uploader import views as uploader_views
from classroom.views import classroom, students, teachers
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import static, staticfiles_urlpatterns
from django.urls import include, path
from django.views.decorators.cache import never_cache
from . import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('classroom.urls')),
    path('about-us/', classroom.about, name='about_us'),
    path('activate-student/<str:uidb64>/<str:token>', students.activate, name='activate_student'),
    path('activate-teacher/<str:uidb64>/<str:token>', teachers.activate, name='activate_teacher'),
    path('browse-competitions/', classroom.browse_courses, name='browse_courses'),
    path('browse-competitions/<int:subject_pk>/', classroom.browse_courses_subject, name='browse_courses_subject'),
    path('ckeditor/upload/', uploader_views.upload, name='ckeditor_upload'),
    path('ckeditor/browse/', never_cache(uploader_views.browse), name='ckeditor_browse'),
    path('contact-us/', classroom.contact_us, name='contact_us'),
    path('competitions/details/<int:pk>/', classroom.CourseDetailView.as_view(), name='course_details'),
    path('competitions/details/<int:pk>/lesson', students.LessonListView.as_view(), name='lesson_list'),
    #path('django-admin/', admin.site.urls),
    path('login/', classroom.login_view, name='login'),
    path('logout/', classroom.logout_view, name='logout'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'),
         name='password_reset_complete'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('ratings/', include('star_ratings.urls', namespace='ratings')),
    path('register/', classroom.register_page, name='register'),
    path('register/sportsman/', students.register, name='student_register'),
    path('register/org/', teachers.register, name='teacher_register')
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)