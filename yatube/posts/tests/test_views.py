import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User, Follow
from .constants import (
    INDEX_URL_NAME,
    GROUP_LIST_URL_NAME,
    PROFILE_URL_NAME,
    POST_DETAIL_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_CREATE_URL_NAME,
    PROFILE_FOLLOW_URL_NAME,
    FOLLOW_INDEX_URL_NAME,
    PROFILE_UNFOLLOW_URL_NAME,
    IMAGE_PNG
)

TEST_OF_POST = 13
POST_LIMIT = 10
MIN_POST_LIMIT = 3

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='kir')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.fail_group = Group.objects.create(
            title='fail-group',
            slug='fail-group',
            description='Тестовое описание пустой группы',
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.png',
            content=IMAGE_PNG,
            content_type='image/png'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.INDEX_URL_REVERSE = reverse(INDEX_URL_NAME)
        cls.FOLLOW_INDEX_URL_REVERSE = reverse(FOLLOW_INDEX_URL_NAME)
        cls.GROUP_LIST_URL_REVERSE = reverse(
            GROUP_LIST_URL_NAME,
            kwargs={'slug': cls.group.slug})
        cls.FAIL_GROUP_LIST_URL_REVERSE = reverse(
            GROUP_LIST_URL_NAME, kwargs={'slug': cls.fail_group.slug})
        cls.PROFILE_URL_REVERSE = reverse(
            PROFILE_URL_NAME,
            kwargs={'username': cls.post.author})
        cls.POST_DETAIL_URL_REVERSE = reverse(
            POST_DETAIL_URL_NAME,
            kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_URL_REVERSE = reverse(
            POST_EDIT_URL_NAME,
            kwargs={'post_id': cls.post.id})
        cls.POST_CREATE_URL_REVERSE = reverse(POST_CREATE_URL_NAME)
        cls.PROFILE_UNFOLLOW_URL_REVERSE = reverse(
            PROFILE_UNFOLLOW_URL_NAME,
            kwargs={'username': cls.not_author})
        cls.PROFILE_FOLLOW_URL_REVERSE = reverse(
            PROFILE_FOLLOW_URL_NAME,
            kwargs={'username': cls.not_author})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_client = Client()
        self.another_client.force_login(self.not_author)
        cache.clear()

    def test_post_in_correct_pages(self):
        """Пост отображается на необходимых страницах."""
        urls_names = (
            self.INDEX_URL_REVERSE,
            self.GROUP_LIST_URL_REVERSE,
            self.PROFILE_URL_REVERSE,
            self.POST_DETAIL_URL_REVERSE,
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if url == self.POST_DETAIL_URL_REVERSE:
                    post = response.context['post']
                else:
                    post = response.context['page_obj'][0]
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.id, post.id)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.image, post.image)

    def test_groups_list_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.GROUP_LIST_URL_REVERSE)
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(
            response.context['group'].description, self.group.description
        )
        self.assertEqual(response.context['group'].slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.PROFILE_URL_REVERSE)
        self.assertEqual(
            response.context['author'], self.post.author)

    def test_forms_correct(self):
        """Шаблоны post_edit и create_post сформированы
        с правильным контекстом"""
        urls_names = (
            self.POST_EDIT_URL_REVERSE,
            self.POST_CREATE_URL_REVERSE
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField)

    def test_new_post_with_group_checking(self):
        """Созданный пост отобразился на: на главной странице сайта,
        на странице выбранной группы,
        в профайле пользователя.
        """
        urls_names = (
            self.INDEX_URL_REVERSE,
            self.GROUP_LIST_URL_REVERSE,
            self.PROFILE_URL_REVERSE
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertContains(response, self.post.text)

    def test_post_with_group_not_in_new_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        response = self.authorized_client.get(self.FAIL_GROUP_LIST_URL_REVERSE)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_caches_in_index(self):
        '''Тестирование кэша в index'''
        post = Post.objects.create(
            text='Текст',
            author=self.user)
        response = self.authorized_client.get(self.INDEX_URL_REVERSE)
        post.delete()
        response2 = self.authorized_client.get(self.INDEX_URL_REVERSE)
        self.assertEqual(response.content, response2.content,)
        cache.clear()
        response3 = self.authorized_client.get(self.INDEX_URL_REVERSE)
        self.assertNotEqual(response2.content, response3.content,)

    def test_follow_for_auth_user(self):
        '''Авторизованный пользователь может подписываться на
        других пользователей.'''
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(self.PROFILE_FOLLOW_URL_REVERSE)
        follow = Follow.objects.all().latest('id')
        self.assertRedirects(
            response,
            self.FOLLOW_INDEX_URL_REVERSE
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author.id, self.not_author.id)
        self.assertEqual(follow.user.id, self.user.id)

    def test_unfollow_for_auth_user(self):
        '''Пользователь может удалять из подписки.'''
        Follow.objects.create(
            user=self.user,
            author=self.not_author)
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            self.PROFILE_UNFOLLOW_URL_REVERSE)
        self.assertRedirects(response, self.FOLLOW_INDEX_URL_REVERSE)
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_or_not_on_authors(self):
        """Запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан"""
        Follow.objects.create(
            user=self.user,
            author=self.post.author)
        response = self.authorized_client.get(self.FOLLOW_INDEX_URL_REVERSE)
        self.assertIn(self.post, response.context['page_obj'])
        response2 = self.another_client.get(self.FOLLOW_INDEX_URL_REVERSE)
        self.assertNotIn(self.post, response2.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='kir')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.INDEX_URL_REVERSE = reverse(INDEX_URL_NAME)
        cls.GROUP_LIST_URL_REVERSE = reverse(
            GROUP_LIST_URL_NAME,
            kwargs={'slug': cls.group.slug})
        cls.PROFILE_URL_REVERSE = reverse(
            PROFILE_URL_NAME,
            kwargs={'username': cls.user.username})
        cls.posts: list = []
        for i in range(TEST_OF_POST):
            cls.posts.append(Post(text=f'Тестовый текст {i}',
                                  group=cls.group,
                                  author=cls.user))
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        cache.clear()

    def test_first_and_second_page_contains_ten_and_three_records(self):
        """Проверка: количество постов на
        index, group_list, profile равно 10 и 3."""
        urls_names = (
            self.INDEX_URL_REVERSE,
            self.GROUP_LIST_URL_REVERSE,
            self.PROFILE_URL_REVERSE
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                response_two = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), POST_LIMIT)
                self.assertEqual(
                    len(response_two.context['page_obj']), MIN_POST_LIMIT
                )
