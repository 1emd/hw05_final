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
    POST_COMMENT_URL_NAME

)

PAGE_COUNT = 1

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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Posts с картинкой."""
        image_png = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image.png',
            content=image_png,
            content_type='image/png'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(POST_CREATE_URL_NAME),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            PROFILE_URL_NAME,
            kwargs={'username': self.post.author}))
        self.assertEqual(Post.objects.count(), posts_count + PAGE_COUNT)
        new_post = Post.objects.latest('id')
        self.assertEqual(form_data['text'], new_post.text)
        self.assertEqual(form_data['group'], new_post.group.id)
        self.assertEqual('posts/image.png', new_post.image.name)

    def test_post_edit(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с картинкой"""
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='red_image.png',
            content=test_image,
            content_type='image/png'
        )
        form_data = {
            'text': 'Изменить текст.',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(
                POST_EDIT_URL_NAME,
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                POST_DETAIL_URL_NAME,
                kwargs={'post_id': self.post.id})
        )
        new_post = Post.objects.latest('id')
        self.assertEqual(form_data['text'], new_post.text)
        self.assertEqual(form_data['group'], new_post.group.id)
        self.assertEqual('posts/red_image.png', new_post.image.name)

    def test_auth_user_add_comment(self):
        '''Комментировать посты может только авторизованный пользователь,
        после успешной отправки комментарий появляется на странице поста.'''
        comments_count = Comment.objects.count()
        form_text = {'text': 'Тестовый текст'}
        response_comm = self.authorized_client.post(
            reverse(
                POST_COMMENT_URL_NAME,
                kwargs={'post_id': self.post.id}),
            data=form_text,
            follow=True)
        self.assertRedirects(
            response_comm,
            reverse(
                POST_DETAIL_URL_NAME,
                kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + PAGE_COUNT)
        comment = Comment.objects.latest('id')
        self.assertEqual(form_text['text'], comment.text)
        self.assertEqual(self.user, comment.author)
        self.assertEqual(self.post.id, comment.post_id)
