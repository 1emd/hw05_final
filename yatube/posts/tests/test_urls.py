from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from .constants import (
    INDEX_URL_NAME,
    GROUP_LIST_URL_NAME,
    PROFILE_URL_NAME,
    POST_DETAIL_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_CREATE_URL_NAME,
    INDEX_URL_TEMPLATE,
    GROUP_LIST_URL_TEMPLATE,
    PROFILE_URL_TEMPLATE,
    POST_DETAIL_URL_TEMPLATE,
    POST_EDIT_URL_TEMPLATE,
    POST_CREATE_URL_TEMPLATE,
    PAGE_NOT_FOUND_TEMPLATE
)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы',
        )

        cls.user = User.objects.create_user(
            username='user_kir')
        cls.another_user = User.objects.create_user(
            username='another_user')

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.index_urls = reverse(INDEX_URL_NAME)
        cls.group_list_url = reverse(
            GROUP_LIST_URL_NAME,
            kwargs={'slug': cls.group.slug}
        )
        cls.profile_url = reverse(
            PROFILE_URL_NAME,
            kwargs={'username': cls.user}
        )
        cls.post_detail_url = reverse(
            POST_DETAIL_URL_NAME,
            kwargs={'post_id': cls.post.id}
        )
        cls.post_edit_url = reverse(
            POST_EDIT_URL_NAME,
            kwargs={'post_id': cls.post.id}
        )
        cls.post_create_url = reverse(POST_CREATE_URL_NAME)
        cls.public_urls = {
            (cls.index_urls, INDEX_URL_TEMPLATE, HTTPStatus.OK),
            (cls.group_list_url, GROUP_LIST_URL_TEMPLATE, HTTPStatus.OK),
            (cls.profile_url, PROFILE_URL_TEMPLATE, HTTPStatus.OK),
            (cls.post_detail_url, POST_DETAIL_URL_TEMPLATE, HTTPStatus.OK),
            (cls.post_edit_url, POST_EDIT_URL_TEMPLATE, HTTPStatus.FOUND),
            (cls.post_create_url, POST_CREATE_URL_TEMPLATE, HTTPStatus.FOUND),
        }
        cls.unex_page = {
            ('/unexisting_page/', '', HTTPStatus.NOT_FOUND)
        }
        cls.author_urls = {
            (cls.post_edit_url, POST_EDIT_URL_TEMPLATE, HTTPStatus.OK),
            (cls.post_create_url, POST_CREATE_URL_TEMPLATE, HTTPStatus.OK),
        }
        cls.auth_urls = {
            (cls.post_edit_url, POST_EDIT_URL_TEMPLATE, HTTPStatus.FOUND),
            (cls.post_create_url, POST_CREATE_URL_TEMPLATE, HTTPStatus.OK),
        }

    def setUp(self):
        self.guest = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.another_user)

    def test_guest_user_urls_status_code(self):
        """Проверка доступности адресов для неавторизованного пользователя."""
        for url, _, response_code in self.public_urls and self.unex_page:
            with self.subTest(url=url):
                status_code = self.guest.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_author_user_urls_status_code(self):
        """Проверка доступности адресов для автора."""
        for url, _, response_code in self.author_urls:
            with self.subTest(url=url):
                status_code = self.post_author.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_authorized_user_urls_status_code(self):
        """Проверка доступности адресов для авторизованного пользователя."""
        for url, _, response_code in self.auth_urls:
            with self.subTest(url=url):
                status_code = self.authorized_user.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for adress, template, _ in self.public_urls:
            with self.subTest(adress=adress):
                response = self.post_author.get(adress)
                self.assertTemplateUsed(response, template)

    def test_404_page(self):
        """Страница с ошибкой 404 отдаёт кастомный шаблон."""
        response = self.post_author.get(self.unex_page)
        self.assertTemplateUsed(response, PAGE_NOT_FOUND_TEMPLATE)
