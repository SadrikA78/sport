from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Avg
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import ListView, UpdateView
from os.path import splitext
from .raw_sql import get_taken_quiz
from ..decorators import student_required
from ..forms import (StudentInterestsForm, StudentProfileForm,
                     StudentSignUpForm, TakeQuizForm, UserUpdateForm)
from ..models import (Answer, Course, Lesson, MyFile, Quiz, Question,
                      Student, StudentAnswer, TakenCourse, TakenQuiz,
                      User, UserLog)
from ..tokens import account_activation_token


@method_decorator([login_required, student_required], name='dispatch')
class ChangePassword(PasswordChangeView):
    success_url = reverse_lazy('students:profile')
    template_name = 'classroom/change_password.html'

    def form_valid(self, form):
        UserLog.objects.create(action='Изменен пароль',
                               user_type='student',
                               user=self.request.user)

        messages.success(self.request, 'Ваш пароль изменен!')
        return super().form_valid(form)


@method_decorator([login_required], name='dispatch')
class LessonListView(ListView):
    model = Lesson
    context_object_name = 'lessons'
    template_name = 'classroom/students/lessons.html'
    paginate_by = 1

    def get_queryset(self, **kwargs):
        return Lesson.objects.select_related('quizzes') \
            .select_related('course') \
            .filter(course__id=self.kwargs['pk']) \
            .order_by('number')

    def get_context_data(self, **kwargs):
        course = Course.objects.values('id', 'title').get(id=self.kwargs['pk'])
        kwargs['title'] = f"{course['title']} Lessons"

        return super().get_context_data(**kwargs)


@method_decorator([login_required, student_required], name='dispatch')
class MyCoursesListView(ListView):
    model = TakenCourse
    ordering = ('title', )
    context_object_name = 'taken_courses'
    extra_context = {
        'title': 'Мои секции',
    }
    template_name = 'classroom/students/mycourses_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_courses \
            .select_related('course', 'course__subject') \
            .filter(status__in=['enrolled', 'pending', 'finished']) \
            .filter(course__status='approved') \
            .order_by('course__title')

        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'classroom/students/interests_form.html'
    success_url = reverse_lazy('students:mycourses_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        UserLog.objects.create(action='Обновлены спортивные интересы',
                               user_type='student',
                               user=self.request.user)

        messages.success(self.request, 'Направленность изменена!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    extra_context = {
        'title': 'Мои пройденные опросы'
    }
    template_name = 'classroom/students/taken_quiz_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['grade'] = TakenQuiz.objects.filter(student_id=self.request.user.pk).aggregate(average=Avg('score'))

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz') \
            .order_by('-id')
        return queryset


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
            'message': 'Ваш аккаунт активирован.',
            'alert': 'success'
        }
    else:
        context = {
            'title': 'Активация аккаунта',
            'result': 'К сожалению, ...',
            'message': 'Активация не завершена. Попробуйте еще раз.',
            'alert': 'danger'
        }
    return render(request, 'authentication/activation.html', context)


@login_required
@student_required
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    student = request.user.student
    take = TakenCourse.objects.create(student=student, course=course)
    take.save()
    UserLog.objects.create(action=f'Отправлен запрос на регистрацию в : {course.title}',
                           user_type='student',
                           user=request.user)

    messages.info(request, 'Вы отправили запрос на мероприятие.')
    return redirect('course_details', pk)


@login_required
@student_required
def unenroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    student = request.user.student
    TakenCourse.objects.filter(student=student, course=course).delete()

    UserLog.objects.create(action=f'Не зарегестрирован : {course.title}',
                           user_type='student',
                           user=request.user)

    messages.success(request, 'Вы отписались от мероприятия')
    return redirect('course_details', pk)


@login_required
def file_view(request, pk):
    file = get_object_or_404(MyFile, pk=pk)
    file_path = str(file.file)
    file_type = ''

    try:
        # Get the file extension:
        extension = splitext(file_path[16:])[1]
        if extension == '.pdf':
            file_type = 'application/pdf'

        response = FileResponse(open(f'media/{file_path}', 'rb'), content_type=file_type)
        response['Content-Disposition'] = f'filename={file_path[16:]}'

        return response
    except FileNotFoundError:
        raise Http404()


@login_required
@student_required
def profile(request):
    if request.method == 'POST':
        user_update_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = StudentProfileForm(request.POST, request.FILES, instance=request.user.student)

        if user_update_form.is_valid() and profile_form.is_valid():
            user_update_form.save()
            profile_form.save()

            UserLog.objects.create(action='Обновлен профиль',
                                   user_type='student',
                                   user=request.user)

            messages.success(request, 'Ваш аккаунт обновлен!')
            return redirect('students:profile')

    else:
        user_update_form = UserUpdateForm(instance=request.user)
        profile_form = StudentProfileForm(instance=request.user.student)

    context = {
        'u_form': user_update_form,
        'p_form': profile_form,
        'title': 'Мой профиль'
    }

    return render(request, 'classroom/profile.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = StudentSignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.is_active = True
                user.save()
                context = {
                        'title': 'Активация аккаунта',
                        'result': 'Внимание',
                        'message': 'Аккаунт участника зарегестрирован',
                        'alert': 'info'
                    }
                # # Send an email to the user with the token:
                # mail_subject = 'СПО ПАК-П: Активация аккаунта.'
                # current_site = get_current_site(request)

                # message = render_to_string('authentication/email_student_confirm.html', {
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
                        # 'message': 'Пожалуйста заполните все поля для активации.',
                        # 'alert': 'info'
                    # }
                # except Exception:
                    # context = {
                        # 'title': 'Активация аккаунта',
                        # 'result': 'Внимание!',
                        # 'message': 'Что-то пошло не так. Попробуйте еще раз.',
                        # 'alert': 'danger'
                    # }

                return render(request, 'authentication/activation.html', context)
        else:
            form = StudentSignUpForm()

    context = {
        'form': form,
        'user_type': 'Участник',
        'title': 'Зарегестрирован как участник'
    }
    return render(request, 'authentication/register_form.html', context)


@login_required
@student_required
def take_quiz(request, course_pk, quiz_pk):
    course = get_object_or_404(Course, pk=course_pk)
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    student = request.user.student

    if student.quizzes.filter(pk=quiz_pk).exists():
        messages.error(request, 'Извините, Вы не выбрали опрос! '
                                'Вы можете посмотреть результаты на странице.')
        return redirect('course_details', course_pk)

    total_questions = quiz.questions.count()
    if total_questions == 0:
        messages.error(request, 'К сожалению, нет данных по пройденному опросу.')
        return redirect('course_details', course_pk)

    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', course_pk, quiz_pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz,
                                                                  answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, course=course,
                                             score=score)

                    UserLog.objects.create(action=f'Выполнен опрос: {quiz.title}',
                                           user_type='student',
                                           user=request.user)

                    messages.success(request, f'Congratulations! You completed the '
                                              f'quiz { quiz.title }! Your grade is { score }%.')

                    # Count the taken quizzes and quizzes:
                    taken_quiz_count = TakenQuiz.objects.filter(student_id=request.user.pk, course=course) \
                        .values_list('id', flat=True).count()
                    quiz_count = Quiz.objects.filter(course_id=course_pk) \
                        .values_list('id', flat=True).count()

                    # Check if the taken quizzes and quizzes have equal count:
                    if taken_quiz_count == quiz_count:
                        TakenCourse.objects.filter(course_id=course_pk, student_id=request.user.pk).update(status='finished')

                    return redirect('course_details', course_pk)
    else:
        form = TakeQuizForm(question=question)

    context = {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    }

    return render(request, 'classroom/students/take_quiz_form.html', context)


@login_required
@student_required
def taken_quiz_result(request, taken_pk, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    questions = Question.objects.filter(quiz=quiz)
    taken_quiz = get_object_or_404(TakenQuiz, pk=taken_pk, quiz=quiz, student_id=request.user.pk)

    student_answers = StudentAnswer.objects\
        .raw(get_taken_quiz(request.user.pk, taken_quiz.pk))

    taken_quiz = TakenQuiz.objects \
        .select_related('quiz') \
        .filter(student=request.user.student, id=taken_quiz.pk, quiz=quiz) \
        .first()

    answers = Answer.objects.filter(question__in=questions)

    context = {
        'title': 'Результат опроса',
        'student_answers': student_answers,
        'taken_quiz': taken_quiz,
        'answers': answers,
        'ownership': 'Your'
    }

    return render(request, 'classroom/students/taken_quiz_result.html', context)