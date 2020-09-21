from django.urls import include, path
from .views import classroom, staff, students, teachers

urlpatterns = [
    path('', classroom.home, name='home'),

    path('staff/', include(([
        path('', staff.dashboard, name='dashboard'),
        path('anal/', staff.anal, name='dashboard_anal'),
        path('account/', staff.account, name='account'),
        path('account/change-password/', staff.ChangePassword.as_view(), name='change_password'),
        path('admin-accounts/', staff.AdminListView.as_view(), name='admin_list'),
        path('admin-accounts/add/', staff.AdminCreateView.as_view(), name='admin_add'),
        path('admin-accounts/<int:pk>/delete/', staff.deactivate_admin, name='admin_deactivate'),
        path('competition-requests/', staff.CourseRequestsView.as_view(), name='course_requests'),
        path('competition-requests/accept/<int:course_pk>/', staff.accept_course, name='accept_course'),
        path('competition-requests/reject/<int:course_pk>/', staff.reject_course, name='reject_course'),
        path('competition/', staff.CourseListView.as_view(), name='course_list'),
        path('competition/<int:course_pk>/delete/', staff.delete_course, name='course_delete'),
        path('get-user-activities/', staff.get_user_activities, name='get_user_activities'),
        path('get-competition-status/', staff.get_course_status, name='get_course_status'),
        path('sportsman/', staff.StudentListView.as_view(), name='student_list'),
        path('sportsman/<int:pk>/delete/', staff.deactivate_student, name='teacher_deactivate'),
        path('subjects/', staff.SubjectListView.as_view(), name='subject_list'),
        path('subjects/add/', staff.SubjectCreateView.as_view(), name='subject_add'),
        path('subjects/<int:pk>/', staff.SubjectUpdateView.as_view(), name='subject_change'),
        path('subjects/<int:pk>/delete/', staff.delete_subject, name='subject_delete'),
        path('org/', staff.TeacherListView.as_view(), name='teacher_list'),
        path('org/<int:pk>/delete/', staff.deactivate_teacher, name='teacher_deactivate'),
        path('user-log/', staff.UserLogListView.as_view(), name='user_log_list'),
        path('user-log/<int:pk>/delete/', staff.delete_log, name='user_log_delete')
    ], 'classroom'), namespace='staff')),

    path('sportsman/', include(([
        path('', students.MyCoursesListView.as_view(), name='mycourses_list'),
        path('change-password/', students.ChangePassword.as_view(), name='change_password'),
        path('competition/<int:course_pk>/quiz/<int:quiz_pk>/', students.take_quiz, name='take_quiz'),
        path('enroll/<int:pk>/', students.enroll, name='enroll'),
        path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        path('profile/', students.profile, name='profile'),
        path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        path('taken/<int:taken_pk>/quiz/<int:quiz_pk>/', students.taken_quiz_result, name='taken_quiz_detail'),
        path('unenroll/<int:pk>/', students.unenroll, name='unenroll'),
        path('view-file/<int:pk>/', students.file_view, name='view_file')
    ], 'classroom'), namespace='students')),

    path('org/', include(([
        path('', teachers.CourseListView.as_view(), name='course_change_list'),
        path('qr/<int:course_pk>/meet/<int:lesson_pk>/',
             teachers.qr, name='qr'),
        path('ajax/load-lessons/', teachers.load_lessons, name='ajax_load_lessons'),
        path('change-password/', teachers.ChangePassword.as_view(), name='change_password'),
        path('competition/add/', teachers.CourseCreateView.as_view(), name='course_add'),
        path('competition/<int:pk>/', teachers.CourseUpdateView.as_view(), name='course_change'),
        path('competition/<int:pk>/delete/', teachers.delete_course,name='course_delete'),
        path('competition/<int:course_pk>/meet/<int:lesson_pk>/',
             teachers.edit_lesson, name='lesson_edit'),
        
        path('competition/<int:course_pk>/meet/<int:lesson_pk>/delete/',
             teachers.delete_lesson, name='lesson_delete'),
        path('competition/<int:course_pk>/quiz/<int:quiz_pk>/',
             teachers.edit_quiz, name='quiz_edit'),
        path('competition/<int:course_pk>/quiz/<int:quiz_pk>/question/add/',
             teachers.add_question, name='question_add'),
        path('competition/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/',
             teachers.edit_question, name='question_change'),
        path('competition/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/delete/',
             teachers.delete_question, name='question_delete'),
        path('enrollment-requests/', teachers.EnrollmentRequestsListView.as_view(),
             name='enrollment_requests_list'),
        path('enrollment-requests/accept/<int:taken_course_pk>', teachers.accept_enrollment,
             name='enrollment_accept'),
        path('enrollment-requests/reject/<int:taken_course_pk>', teachers.reject_enrollment,
             name='enrollment_reject'),
        path('files/', teachers.FilesListView.as_view(), name='file_list'),
        path('files/add/', teachers.add_files, name='file_add'),
        path('files/<int:file_pk>/delete/', teachers.delete_file,
             name='delete_file'),
        path('meet/', teachers.LessonListView.as_view(), name='lesson_list'),
        path('meet/add/', teachers.add_lesson, name='lesson_add'),
        path('meet/<int:lesson_pk>/delete/', teachers.delete_lesson_from_list,
             name='delete_lesson_from_list'),
        path('profile/', teachers.profile, name='profile'),
        path('quiz/', teachers.QuizListView.as_view(), name='quiz_list'),
        path('quiz/add/', teachers.add_quiz, name='quiz_add'),
        path('quiz/<int:quiz_pk>/delete/', teachers.delete_quiz_from_list,
             name='delete_quiz_from_list'),
        path('quiz/<int:quiz_pk>/delete/', teachers.delete_quiz, name='quiz_delete'),
        path('quiz/<int:pk>/results/', teachers.QuizResultsView.as_view(), name='quiz_results'),
        path('quiz/<int:quiz_pk>/results/<int:student_pk>/taken/<int:taken_pk>',
             teachers.quiz_result_detail, name='quiz_result_detail')
    ], 'classroom'), namespace='teachers')),
]