from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import (CreateView, DetailView, ListView,
                                  UpdateView)
from .raw_sql import get_taken_quiz
from ..decorators import teacher_required
from ..forms import (BaseAnswerInlineFormSet, CourseAddForm, FileAddForm,
                     LessonAddForm, LessonEditForm, QuizAddForm, QuizEditForm,
                     QuestionForm, TeacherProfileForm, TeacherSignUpForm,
                     UserUpdateForm)
from ..models import (Answer, Course, MyFile, Lesson, Question, Quiz,
                      StudentAnswer, TakenCourse, TakenQuiz, User, UserLog, UserTel)
from ..tokens import account_activation_token
from star_ratings.models import Rating
import os

import qrcode
from django.http import HttpResponse, HttpResponseRedirect, Http404

def get_enrollment_requests_count(user):
    owned_courses = Course.objects.values_list('id', flat=True) \
        .filter(owner=user)
    return TakenCourse.objects.values_list('id', flat=True) \
        .filter(course__in=owned_courses,
                status='pending').count()


@method_decorator([login_required, teacher_required], name='dispatch')
class ChangePassword(PasswordChangeView):
    success_url = reverse_lazy('teachers:profile')
    template_name = 'classroom/change_password.html'

    def form_valid(self, form):
        UserLog.objects.create(action='Изменен пароль',
                               user_type='teacher',
                               user=self.request.user)

        messages.success(self.request, 'Вы успешно изменили пароль!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseCreateView(CreateView):
    model = Course
    form_class = CourseAddForm
    template_name = 'classroom/teachers/course_add_form.html'
    extra_context = {
        'title': 'Новая секция'
    }

    def form_valid(self, form):
        course = form.save(commit=False)
        course.owner = self.request.user
        course.save()
        Rating.objects.create(count=0, total=0, average=0, object_id=course.pk, content_type_id=15)

        UserLog.objects.create(action=f'Created the course: {course.title}',
                               user_type='teacher',
                               user=self.request.user)

        messages.success(self.request, 'Секция создана успешно!')
        return redirect('teachers:course_change_list')

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    extra_context = {
        'title': 'Мои секции'
    }
    template_name = 'classroom/teachers/course_list.html'

    def get_context_data(self, **kwargs):
        """Get only the courses that the logged in teacher owns,
        count the enrolled students, and order by title"""
        kwargs['courses'] = self.request.user.courses \
            .exclude(status__iexact='deleted') \
            .annotate(taken_count=Count('taken_courses',
                                        filter=Q(taken_courses__status='enrolled'),
                                        distinct=True)) \
            .order_by('title')

        # enrollment_request_count is used for base.html's navbar.
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseUpdateView(UpdateView):
    model = Course
    form_class = CourseAddForm
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_change_form.html'
    extra_context = {
        'title': 'Редактировать секцию'
    }

    def form_valid(self, form):
        course = form.save(commit=False)
        course.status = 'pending'
        course.save()

        UserLog.objects.create(action=f'Edited the course: {course.title}',
                               user_type='teacher',
                               user=self.request.user)

        messages.success(self.request, f'{course.title} has been successfully updated.')
        return redirect('teachers:course_change_list')

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """This method is an implicit object-level permission management.
        This view will only match the ids of existing courses that belongs
        to the logged in user."""
        return self.request.user.courses.exclude(status='deleted')


@method_decorator([login_required, teacher_required], name='dispatch')
class EnrollmentRequestsListView(ListView):
    model = Course
    context_object_name = 'taken_courses'
    extra_context = {
        'title': 'Запросы на участие в мероприятии'
    }
    template_name = 'classroom/teachers/enrollment_requests_list.html'

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """This method gets the enrollment requests of students."""
        return TakenCourse.objects.filter(course__in=self.request.user.courses.all(),
                                          status='pending')


@method_decorator([login_required, teacher_required], name='dispatch')
class FilesListView(ListView):
    model = MyFile
    context_object_name = 'files'
    extra_context = {
        'title': 'Мои файлы'
    }
    template_name = 'classroom/teachers/file_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.my_files.all() \
            .exclude(course__status='deleted') \
            .order_by('-id')


@method_decorator([login_required, teacher_required], name='dispatch')
class LessonListView(ListView):
    model = Lesson
    context_object_name = 'lessons'
    extra_context = {
        'title': 'Мои мероприятия'
    }
    template_name = 'classroom/teachers/lesson_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets the lesson that the user owns through course FK."""
        return Lesson.objects.filter(course__in=self.request.user.courses.all()) \
            .exclude(course__status='deleted') \
            .order_by('-id')


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    context_object_name = 'quizzes'
    extra_context = {
        'title': 'Мои опросы'
    }
    template_name = 'classroom/teachers/quiz_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """enrollment_request_count is used for base.html's navbar."""
        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets the quizzes that the logged in teacher owns.
        Counts the questions and the number of students who took the quiz."""
        queryset = Quiz.objects.filter(course__owner=self.request.user) \
            .exclude(course__status='deleted') \
            .annotate(questions_count=Count('questions', distinct=True)) \
            .annotate(taken_count=Count('taken_quizzes', distinct=True)) \
            .order_by('-id')
        return queryset


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizResultsView(DetailView):
    model = Quiz
    context_object_name = 'quiz'
    extra_context = {
        'title': 'Результаты опроса'
    }
    template_name = 'classroom/teachers/quiz_results.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes = quiz.taken_quizzes.select_related('student__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_quizzes': taken_quizzes,
            'total_taken_quizzes': total_taken_quizzes,
            'quiz_score': quiz_score
        }
        kwargs.update(extra_context)

        kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return Quiz.objects.filter(course__in=Course.objects.filter(owner=self.request.user))


class TeacherSignUpView(CreateView):
    model = User
    form_class = TeacherSignUpForm
    template_name = 'authentication/register_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('teachers:quiz_change_list')


@login_required
@teacher_required
def accept_enrollment(request, taken_course_pk):
    taken_course_get = get_object_or_404(TakenCourse, pk=taken_course_pk)
    TakenCourse.objects.filter(id=taken_course_get.pk).update(status='enrolled')

    UserLog.objects.create(action='Принят запрос на регистрацию',
                           user_type='teacher',
                           user=request.user)

    messages.success(request, 'Спортсмен добавлен.')
    return redirect('teachers:enrollment_requests_list')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        # activate user and login:
        user.is_active = True
        user.save()
        login(request, user)
        context = {
            'title': 'Активация аккаунта',
            'result': 'Поздравляем!',
            'message': 'Ваш аккаунт успешно активирован.',
            'alert': 'success'
        }
    else:
        context = {
            'title': 'Активация аккаунта',
            'result': 'К сожалению,...',
            'message': 'Активация временно не возможна. Попробуйте еще раз.',
            'alert': 'danger'
        }
    return render(request, 'authentication/activation.html', context)


@login_required
@teacher_required
def add_files(request):
    if request.method == 'POST':
        form = FileAddForm(request.user, data=request.POST, files=request.FILES)
        success = None
        if form.is_valid():
            for file in request.FILES.getlist('file'):
                extension = os.path.splitext(str(request.FILES['file']))[1]
                # Check the file extensions:
                if extension == '.pdf'or \
                        extension == '.doc' or \
                        extension == '.docx' or \
                        extension == '.ppt' or \
                        extension == '.pptx':

                    # For every file selected in the upload, create a record in File table:
                    MyFile.objects.create(file=file, course=form.cleaned_data['course'], owner=request.user)
                    success = True

            if success:
                UserLog.objects.create(action='Загружены файлы',
                                       user_type='teacher',
                                       user=request.user)
                messages.success(request, 'Файлы обновлены.')
                return redirect('teachers:file_list')
            else:
                messages.error(request, 'Только файлы: .pdf, .doc, .docx, .ppt, and .pptx.')
                return redirect('teachers:file_add')

        else:
            if not request.FILES:
                messages.error(request, 'Выберете файл.')
                return redirect('teachers:file_add')

    else:
        form = FileAddForm(current_user=request.user)

    context = {
        'form': form,
        'title': 'Добавить файл',
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }
    return render(request, 'classroom/teachers/file_add_form.html', context)


@login_required
@teacher_required
def add_lesson(request):
    if request.method == 'POST':
        form = LessonAddForm(request.user, data=request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()

            UserLog.objects.create(action=f'Создано мероприятие: {lesson.title}',
                                   user_type='teacher',
                                   user=request.user)
            messages.success(request, 'Билеты на мероприятия созданы.')
            return redirect('teachers:lesson_list')
    else:
        form = LessonAddForm(current_user=request.user)

    context = {
        'form': form,
        'title': 'Добавить мероприятие',
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }
    return render(request, 'classroom/teachers/lesson_add_form.html', context)


@login_required
@teacher_required
def add_question(request, course_pk, quiz_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course=course)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()

            UserLog.objects.create(action=f'Добавлен вопрос в опросник: {quiz.title}',
                                   user_type='teacher',
                                   user=request.user)
            messages.success(request, 'Можете добавить вопросы опроса.')
            return redirect('teachers:question_change', quiz.course.pk, quiz.pk, question.pk)
    else:
        form = QuestionForm()

    context = {
        'title': 'Добавить вопрос',
        'quiz': quiz,
        'form': form,
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }
    return render(request, 'classroom/teachers/question_add_form.html', context)


@login_required
@teacher_required
def add_quiz(request):
    if request.method == 'POST':
        form = QuizAddForm(request.user, data=request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.save()

            UserLog.objects.create(action=f'Создан опрос: {quiz.title}',
                                   user_type='teacher',
                                   user=request.user)
            messages.success(request, 'Опрос успешно создан. Вы можете добавить вопросы.')
            return redirect('teachers:quiz_edit', quiz.course.pk, quiz.pk)
    else:
        form = QuizAddForm(current_user=request.user)

    context = {
        'form': form,
        'title': 'Добавить опрос',
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }
    return render(request, 'classroom/teachers/quiz_add_form.html', context)


@login_required
@teacher_required
def delete_course(request, pk):
    course_get = get_object_or_404(Course, pk=pk)
    course = request.user.courses.get(id=course_get.pk)
    course.status = 'deleted'
    course.save()

    UserLog.objects.create(action=f'Мероприятие удалено: {course.title}',
                           user_type='teacher',
                           user=request.user)
    messages.success(request, 'Секция удалена.')

    return redirect('teachers:course_change_list')


@login_required
@teacher_required
def delete_file(request, file_pk):
    teacher = request.user
    file_get = get_object_or_404(MyFile, pk=file_pk)
    file_name = MyFile.objects.values_list('file', flat=True).get(id=file_get.pk)
    # delete from the database
    MyFile.objects.get(id=file_pk, course__owner=teacher).delete()
    # remove from the folder
    os.remove(os.path.join('media', file_name))

    UserLog.objects.create(action=f'Удален файл: {str(file_get.file)[16:]}',
                           user_type='teacher',
                           user=request.user)
    messages.success(request, 'Файл удален.')

    return redirect('teachers:file_list')


@login_required
@teacher_required
def delete_lesson(request, course_pk, lesson_pk):
    teacher = request.user
    lesson_get = get_object_or_404(Lesson, pk=lesson_pk)
    Lesson.objects.filter(id=lesson_get.pk, course__owner=teacher).delete()

    UserLog.objects.create(action=f'Удалено мероприятие: {lesson_get.title}',
                           user_type='teacher',
                           user=request.user)
    messages.success(request, 'Мероприятие удалено.')

    return redirect('course_details', course_pk)


@login_required
@teacher_required
def delete_lesson_from_list(request, lesson_pk):
    lesson_get = get_object_or_404(Lesson, pk=lesson_pk)
    Lesson.objects.filter(id=lesson_pk, course__owner=request.user).delete()
    messages.success(request, 'Мероприятие удалено.')

    UserLog.objects.create(action=f'Удалено мероприятие: {lesson_get.title}',
                           user_type='teacher',
                           user=request.user) 
    
    return redirect('teachers:lesson_list')


@login_required
@teacher_required
def delete_question(request, course_pk, quiz_pk, question_pk):
    teacher = request.user
    quiz_get = get_object_or_404(Quiz, pk=quiz_pk)
    question_get = get_object_or_404(Question, pk=question_pk)
    quiz = Quiz.objects.get(id=quiz_get.pk, course__owner=teacher)
    Question.objects.get(id=question_get.pk, quiz=quiz).delete()

    UserLog.objects.create(action=f'Удален вопрос: {quiz_get.title}',
                           user_type='teacher',
                           user=request.user)

    messages.success(request, 'Мероприятие удалено.')

    return redirect('teachers:quiz_edit', course_pk, quiz_pk)


@login_required
@teacher_required
def delete_quiz(request, quiz_pk):
    teacher = request.user
    quiz_get = get_object_or_404(Quiz, pk=quiz_pk)
    Quiz.objects.filter(id=quiz_get.pk, course__owner=teacher).delete()

    UserLog.objects.create(action=f'Удален опросник: {quiz_get.title}',
                           user_type='teacher',
                           user=request.user)

    messages.success(request, 'Опрос удален.')

    return redirect('teachers:quiz_list')


@login_required
@teacher_required
def delete_quiz_from_list(request, quiz_pk):
    quiz_get = get_object_or_404(Quiz, pk=quiz_pk)
    Quiz.objects.filter(id=quiz_pk, course__owner=request.user).delete()

    UserLog.objects.create(action=f'Удален опросник: {quiz_get.title}',
                           user_type='teacher',
                           user=request.user)

    messages.success(request, 'Опрос удален.')

    return redirect('teachers:quiz_list')


@login_required
@teacher_required
def edit_lesson(request, course_pk, lesson_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)

    if request.method == 'POST':
        form = LessonEditForm(data=request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()

            UserLog.objects.create(action=f'Мероприятие изменено: {lesson.title}',
                                   user_type='teacher',
                                   user=request.user)

            messages.success(request, 'Мероприятие изменено.')
            return redirect('teachers:lesson_list')
    else:
        form = LessonEditForm(instance=lesson)

    context = {
        'course': course,
        'lesson': lesson,
        'form': form,
        'title': 'Изменить мероприятие',
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }
    return render(request, 'classroom/teachers/lesson_change_form.html', context)
@login_required
@teacher_required
def qr(request, course_pk, lesson_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)
    # tel = UserTel.objects.all()
    img = qrcode.make('Some data here')
    #link = "http://osirisvka.ru:1111/?centr="+str(course.title)+"&section="+str(lesson.title)+"&data="+"10 ноября 2019 г."

    response = HttpResponse(content_type="/tmp/")
    img.save(response, "PNG")
    context = {
        'course': course,
        'lesson': lesson,
        #'link':link,
    }
    return render(request, 'classroom/teachers/qr.html', context)


@login_required
@teacher_required
def edit_question(request, course_pk, quiz_pk, question_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course=course)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)

    AnswerFormSet = inlineformset_factory(
        Question,  # parent model
        Answer,  # base model
        formset=BaseAnswerInlineFormSet,
        fields=('text', 'is_correct'),
        min_num=2,
        validate_min=True,
        max_num=10,
        validate_max=True
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()

                UserLog.objects.create(action=f'Изменено: {quiz.title}',
                                       user_type='teacher',
                                       user=request.user)

            messages.success(request, 'Вопрос и ответы сохранены!')
            return redirect('teachers:quiz_edit', course.pk, quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    context = {
        'title': 'Редактировать вопрос',
        'quiz': quiz,
        'question': question,
        'form': form,
        'formset': formset,
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }

    return render(request, 'classroom/teachers/question_change_form.html', context)


@login_required
@teacher_required
def edit_quiz(request, course_pk, quiz_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course=course)
    question = Question.objects.filter(quiz=quiz).annotate(answers_count=Count('answers'))

    if request.method == 'POST':
        form = QuizEditForm(data=request.POST, instance=quiz)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.save()

            UserLog.objects.create(action=f'Изменено: {quiz.title}',
                                   user_type='teacher',
                                   user=request.user)

            messages.success(request, 'опрос изменен.')
            return redirect('teachers:quiz_edit', quiz.course.pk, quiz.pk)
    else:
        form = QuizEditForm(instance=quiz)

    context = {
        'title': 'Редактировать опрос',
        'course': course,
        'quiz': quiz,
        'questions': question,
        'form': form,
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }
    return render(request, 'classroom/teachers/quiz_change_form.html', context)


@login_required
@teacher_required
def load_lessons(request):
    course_id = request.GET.get('course')
    lessons = Lesson.objects.filter(course_id=course_id).order_by('title')
    return render(request, 'classroom/teachers/lesson_dropdown_list_options.html', {'lessons': lessons})


@login_required
@teacher_required
def profile(request):
    if request.method == 'POST':
        user_update_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = TeacherProfileForm(request.POST, request.FILES, instance=request.user.teacher)

        if user_update_form.is_valid() and profile_form.is_valid():
            user_update_form.save()
            profile_form.save()

            UserLog.objects.create(action='Обновить провиль представителя',
                                   user_type='teacher',
                                   user=request.user)

            messages.success(request, 'Аккаунт обновлен!')
            return redirect('teachers:profile')

    else:
        user_update_form = UserUpdateForm(instance=request.user)
        profile_form = TeacherProfileForm(instance=request.user.teacher)

    context = {
        'title': 'Мой профиль',
        'u_form': user_update_form,
        'p_form': profile_form,
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }

    return render(request, 'classroom/profile.html', context)


@login_required
@teacher_required
def quiz_result_detail(request, quiz_pk, student_pk, taken_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    questions = Question.objects.filter(quiz=quiz)
    taken_quiz = get_object_or_404(TakenQuiz, pk=taken_pk, quiz=quiz, student_id=student_pk)

    student_answer = StudentAnswer.objects.raw(
            get_taken_quiz(student_pk, taken_quiz.pk))

    taken_quiz = TakenQuiz.objects \
        .select_related('quiz') \
        .filter(student_id=student_pk, id=taken_quiz.pk, quiz=quiz) \
        .first()

    answers = Answer.objects.filter(question__in=questions)
    student_name = User.objects.get(pk=student_pk)

    context = {
        'title': 'Результат опроса',
        'student_answers': student_answer,
        'taken_quiz': taken_quiz,
        'answers': answers,
        'student_name': student_name,
        'ownership': 'Участник',
        'enrollment_request_count': get_enrollment_requests_count(request.user)
    }

    return render(request, 'classroom/students/taken_quiz_result.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = TeacherSignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.is_active = True
                user.save()
                context = {
                        'title': 'Активация аккаунта',
                        'result': 'Внимание',
                        'message': 'Аккаунт представителя организации зарегистрирован',
                        'alert': 'info'
                    }
                # Send an email to the user with the token:
                # mail_subject = 'СПО ПАК-П: аккаунт активирован.'
                # current_site = get_current_site(request)

                # message = render_to_string('authentication/email_teacher_confirm.html', {
                    # 'user': user,
                    # 'domain': current_site,
                    # 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    # 'token': account_activation_token.make_token(user),
                # })

                # to_email = form.cleaned_data.get('email')
                # email = EmailMessage(mail_subject, message, to=[to_email])
                # try:
                    # email.send()
                    # context = {
                        # 'title': 'Активация аккаунта',
                        # 'result': 'Еще один этап...',
                        # 'message': 'Проверьте свои данные.',
                        # 'alert': 'info'
                    # }
                # except Exception:
                    # context = {
                        # 'title': 'Активация аккаунта',
                        # 'result': 'Внимание',
                        # 'message': 'К сожалению, допущена ошибка. Попробуйте еще раз.',
                        # 'alert': 'warning'
                    # }

                return render(request, 'authentication/activation.html', context)
        else:
            form = TeacherSignUpForm()

    context = {
        'form': form,
        'user_type': 'Представитель организатора',
        'title': 'Зарегистрирован как представитель органиатора соревнований'
    }
    return render(request, 'authentication/register_form.html', context)


@login_required
@teacher_required
def reject_enrollment(request, taken_course_pk):
    taken_course_get = get_object_or_404(TakenCourse, pk=taken_course_pk)
    TakenCourse.objects.filter(id=taken_course_get.pk).delete()

    UserLog.objects.create(action='Отклонен запрос',
                           user_type='teacher',
                           user=request.user)

    messages.success(request, 'Запрос на участие отклонен.')
    return redirect('teachers:enrollment_requests_list')