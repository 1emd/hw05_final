import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

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
    INDEX_URL_TEMPLATE,
    GROUP_LIST_URL_TEMPLATE,
    PROFILE_URL_TEMPLATE,
    POST_DETAIL_URL_TEMPLATE,
    POST_EDIT_URL_TEMPLATE,
    POST_CREATE_URL_TEMPLATE
)

TEST_OF_POST = 13
POST_LIMIT = 10
MIN_POST_LIMIT = 3
PAGE_COUNT = 1

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
        cls.image_png = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.png',
            content=cls.image_png,
            content_type='image/png'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

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

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                INDEX_URL_NAME): INDEX_URL_TEMPLATE,
            reverse(
                GROUP_LIST_URL_NAME,
                kwargs={'slug': self.group.slug}): GROUP_LIST_URL_TEMPLATE,
            reverse(
                PROFILE_URL_NAME,
                kwargs={'username': self.post.author}): PROFILE_URL_TEMPLATE,
            reverse(
                POST_DETAIL_URL_NAME,
                kwargs={'post_id': self.post.id}): POST_DETAIL_URL_TEMPLATE,
            reverse(
                POST_EDIT_URL_NAME,
                kwargs={'post_id': self.post.id}): POST_EDIT_URL_TEMPLATE,
            reverse(
                POST_CREATE_URL_NAME): POST_CREATE_URL_TEMPLATE,
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(INDEX_URL_NAME))
        self.assertEqual(
            response.context['page_obj'][0].text, self.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].author.username, self.user.username
        )
        self.assertEqual(
            response.context['page_obj'][0].group.title, self.group.title
        )
        self.assertEqual(
            response.context['page_obj'][0].image, self.post.image
        )

    def test_groups_list_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                GROUP_LIST_URL_NAME,
                kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(
            response.context['group'].description, self.group.description
        )
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(
            response.context['page_obj'][0].image, self.post.image
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                PROFILE_URL_NAME,
                kwargs={'username': self.post.author})
        )
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response.context['page_obj'][0].author.username,
            self.post.author.username
        )
        self.assertEqual(
            response.context['page_obj'][0].group.title, self.post.group.title
        )
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(
            response.context['page_obj'][0].image, self.post.image
        )

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                POST_DETAIL_URL_NAME,
                kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context['post'].text, self.post.text
        )
        self.assertEqual(
            response.context['post'].author.username, self.post.author.username
        )
        self.assertEqual(
            response.context['post'].group.title, self.post.group.title
        )
        self.assertEqual(
            response.context['post'].image, self.post.image
        )

    def test_forms_correct(self):
        """Шаблоны post_edit и create_post сформированы
        с правильным контекстом"""
        urls_names = {
            reverse(
                POST_EDIT_URL_NAME,
                kwargs={'post_id': self.post.id}),
            reverse(POST_CREATE_URL_NAME)
        }
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
            reverse(INDEX_URL_NAME),
            reverse(
                GROUP_LIST_URL_NAME,
                kwargs={'slug': self.group.slug}),
            reverse(
                PROFILE_URL_NAME,
                kwargs={'username': self.post.author})
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertContains(response, self.post.text)

    def test_post_with_group_not_in_new_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        response = self.authorized_client.get(
            reverse(GROUP_LIST_URL_NAME, kwargs={'slug': self.fail_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_caches_in_index(self):
        '''Тестирование кэша в index'''
        post = Post.objects.create(
            text='Текст',
            author=self.user)
        response = self.authorized_client.get(reverse(INDEX_URL_NAME))
        post.delete()
        response2 = self.authorized_client.get(reverse(INDEX_URL_NAME))
        self.assertEqual(response.content, response2.content,)
        cache.clear()
        response3 = self.authorized_client.get(reverse(INDEX_URL_NAME))
        self.assertNotEqual(response2.content, response3.content,)

    def test_follow_for_auth_user(self):
        '''Авторизованный пользователь может подписываться на
        других пользователей.'''
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse(
                PROFILE_FOLLOW_URL_NAME,
                kwargs={'username': self.not_author}))
        follow = Follow.objects.all().latest('id')
        self.assertRedirects(
            response,
            reverse(FOLLOW_INDEX_URL_NAME)
        )
        self.assertEqual(Follow.objects.count(), follow_count + PAGE_COUNT)
        self.assertEqual(follow.author.id, self.not_author.id)
        self.assertEqual(follow.user.id, self.user.id)

    def test_unfollow_for_auth_user(self):
        '''Пользователь может удалять из подписки.'''
        Follow.objects.create(
            user=self.user,
            author=self.not_author)
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse(
                PROFILE_UNFOLLOW_URL_NAME,
                kwargs={'username': self.not_author}))
        self.assertRedirects(
            response,
            reverse(FOLLOW_INDEX_URL_NAME)
        )
        self.assertEqual(Follow.objects.count(), follow_count - PAGE_COUNT)

    def test_follow_or_not_on_authors(self):
        """Запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан"""
        Follow.objects.create(
            user=self.user,
            author=self.post.author)
        response = self.authorized_client.get(
            reverse(FOLLOW_INDEX_URL_NAME))
        self.assertIn(self.post, response.context['page_obj'])
        response2 = self.another_client.get(
            reverse(FOLLOW_INDEX_URL_NAME))
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
            reverse(INDEX_URL_NAME),
            reverse(
                GROUP_LIST_URL_NAME,
                kwargs={'slug': self.group.slug}),
            reverse(
                PROFILE_URL_NAME,
                kwargs={'username': self.user.username})
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                response_two = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), POST_LIMIT)
                self.assertEqual(
                    len(response_two.context['page_obj']), MIN_POST_LIMIT
                )
