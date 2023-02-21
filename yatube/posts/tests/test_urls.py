from http import HTTPStatus

from django.core.cache import cache
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
    PAGE_NOT_FOUND_TEMPLATE,
    UNEXISTING_PAGE_URL
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
        cls.guest = Client()
        cls.post_author = Client()
        cls.post_author.force_login(cls.user)
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.another_user)
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.INDEX_URL_REVERSE = reverse(INDEX_URL_NAME)
        cls.GROUP_LIST_URL_REVERSE = reverse(
            GROUP_LIST_URL_NAME,
            kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE_URL_REVERSE = reverse(
            PROFILE_URL_NAME,
            kwargs={'username': cls.user}
        )
        cls.POST_DETAIL_URL_REVERSE = reverse(
            POST_DETAIL_URL_NAME,
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL_REVERSE = reverse(
            POST_EDIT_URL_NAME,
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_CREATE_URL_REVERSE = reverse(POST_CREATE_URL_NAME)
        cls.INDEX_DATA = (
            cls.INDEX_URL_REVERSE, INDEX_URL_TEMPLATE,
            cls.guest, HTTPStatus.OK
        )
        cls.GROUP_LIST_DATA = (
            cls.GROUP_LIST_URL_REVERSE, GROUP_LIST_URL_TEMPLATE,
            cls.guest, HTTPStatus.OK)
        cls.PROFILE_DATA = (
            cls.PROFILE_URL_REVERSE, PROFILE_URL_TEMPLATE,
            cls.guest, HTTPStatus.OK
        )
        cls.POST_DETAIL_DATA = (
            cls.POST_DETAIL_URL_REVERSE, POST_DETAIL_URL_TEMPLATE,
            cls.guest, HTTPStatus.OK
        )
        cls.POST_EDIT_DATA = (
            cls.POST_EDIT_URL_REVERSE, POST_EDIT_URL_TEMPLATE,
            cls.guest, HTTPStatus.FOUND
        )
        cls.POST_CREATE_DATA = (
            cls.POST_CREATE_URL_REVERSE, POST_CREATE_URL_TEMPLATE,
            cls.guest, HTTPStatus.FOUND
        )
        cls.POST_EDIT_DATA_FOR_AUTHOR = (
            cls.POST_EDIT_URL_REVERSE, POST_EDIT_URL_TEMPLATE,
            cls.post_author, HTTPStatus.OK
        )
        cls.POST_EDIT_DATA_FOR_AUTH_USER = (
            cls.POST_EDIT_URL_REVERSE, POST_EDIT_URL_TEMPLATE,
            cls.authorized_user, HTTPStatus.FOUND
        )
        cls.POST_CREATE_DATA_FOR_AUTHOR = (
            cls.POST_CREATE_URL_REVERSE, POST_CREATE_URL_TEMPLATE,
            cls.post_author, HTTPStatus.OK
        )
        cls.POST_CREATE_DATA_FOR_AUTH_USER = (
            cls.POST_CREATE_URL_REVERSE, POST_CREATE_URL_TEMPLATE,
            cls.authorized_user, HTTPStatus.OK
        )
        cls.UNEXISTING_DATA = (
            UNEXISTING_PAGE_URL, PAGE_NOT_FOUND_TEMPLATE,
            cls.guest, HTTPStatus.NOT_FOUND
        )

    def setUp(self):
        cache.clear()

    def test_guest_user_urls_status_code(self):
        """Проверка доступности адресов для пользователей."""
        pages = (
            self.INDEX_DATA, self.GROUP_LIST_DATA, self.PROFILE_DATA,
            self.POST_DETAIL_DATA, self.POST_EDIT_DATA,
            self.POST_CREATE_DATA, self.UNEXISTING_DATA,
            self.POST_EDIT_DATA_FOR_AUTHOR,
            self.POST_CREATE_DATA_FOR_AUTHOR,
            self.POST_EDIT_DATA_FOR_AUTH_USER,
            self.POST_CREATE_DATA_FOR_AUTH_USER,
        )
        for url, _, client, response_code in pages:
            with self.subTest(url=url):
                status_code = client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages = (self.INDEX_DATA, self.GROUP_LIST_DATA, self.PROFILE_DATA,
                 self.POST_DETAIL_DATA, self.POST_EDIT_DATA,
                 self.POST_CREATE_DATA, self.UNEXISTING_DATA)
        for url, template, _, _ in pages:
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
