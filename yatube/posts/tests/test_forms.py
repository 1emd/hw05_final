import shutil
import tempfile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Group, Post, User, Comment
from .constants import (
    PROFILE_URL_NAME,
    POST_DETAIL_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_CREATE_URL_NAME,
    POST_COMMENT_URL_NAME,
    IMAGE_PNG,
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='kir')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый новый текст',
            group=cls.group,
        )
        cls.form = PostForm()
        cls.uploaded = SimpleUploadedFile(
            name='image.png',
            content=IMAGE_PNG,
            content_type='image/png'
        )
        cls.new_uploaded = SimpleUploadedFile(
            name='image2.png',
            content=IMAGE_PNG,
            content_type='image/png'
        )
        cls.profile_reverse = reverse(
            PROFILE_URL_NAME,
            kwargs={'username': cls.post.author})
        cls.post_create_reverse = reverse(POST_CREATE_URL_NAME)
        cls.post_edit_reverse = reverse(
            POST_EDIT_URL_NAME,
            kwargs={'post_id': cls.post.id})
        cls.post_detail_reverse = reverse(
            POST_DETAIL_URL_NAME,
            kwargs={'post_id': cls.post.id})
        cls.login_reverse = reverse('login') + '?next='
        cls.post_comment_reverse = reverse(
            POST_COMMENT_URL_NAME,
            kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest = Client()

    def test_create_post(self):
        """Валидная форма создает запись в Posts с картинкой."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            self.post_create_reverse,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.profile_reverse)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.latest('id')
        self.assertEqual(form_data['text'], new_post.text)
        self.assertEqual(form_data['group'], new_post.group.id)
        self.assertEqual(
            form_data['image'].name, new_post.image.name.split('/')[1])

    def test_post_edit(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с картинкой"""
        form_data = {
            'text': 'Изменить текст.',
            'group': self.group.id,
            'image': self.new_uploaded,
        }
        response = self.authorized_client.post(
            self.post_edit_reverse,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            self.post_detail_reverse
        )
        new_post = Post.objects.latest('id')
        self.assertEqual(form_data['text'], new_post.text)
        self.assertEqual(form_data['group'], new_post.group.id)
        self.assertEqual(
            form_data['image'].name, new_post.image.name.split('/')[1])

    def test_not_auth_user_create_post(self):
        '''Невозможность создания поста не авторизированным пользователем.'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.guest.post(
            self.post_create_reverse,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, self.login_reverse + self.post_create_reverse)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_not_auth_user_post_edit(self):
        '''Невозможность редактирования поста
        не авторизированным пользователем.'''
        form_data = {
            'text': 'Пост отредактирован гостем',
        }
        response = self.guest.post(
            self.post_edit_reverse,
            data=form_data, follow=True
        )
        post = Post.objects.latest('id')
        self.assertRedirects(
            response, self.login_reverse + self.post_edit_reverse
        )
        self.assertNotEqual(form_data['text'], post.text)

    def test_not_auth_user_add_comment(self):
        '''Не авторизованный пользователь не может комментировать посты'''
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коментарий'}
        response = self.guest.post(
            self.post_comment_reverse,
            data=form_data,
            follow=True)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response, self.login_reverse + self.post_comment_reverse
        )

    def test_auth_user_add_comment(self):
        '''Комментировать посты может авторизованный пользователь,
        после успешной отправки комментарий появляется на странице поста.'''
        comments_count = Comment.objects.count()
        form_text = {'text': 'Тестовый текст'}
        response_comm = self.authorized_client.post(
            self.post_comment_reverse,
            data=form_text,
            follow=True)
        self.assertRedirects(
            response_comm, self.post_detail_reverse
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = Comment.objects.latest('id')
        self.assertEqual(form_text['text'], comment.text)
        self.assertEqual(self.user, comment.author)
        self.assertEqual(self.post.id, comment.post_id)
