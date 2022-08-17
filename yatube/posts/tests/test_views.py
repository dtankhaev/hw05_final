import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostURLTestPages(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.group_two = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-two',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.author_client = Client()
        self.author_client.force_login(PostURLTestPages.user)
        cache.clear()

    def test_urls_name(self):
        """Проверка на корректное отображение шаблонов по имени"""
        templates_pages_names = {
            reverse('posts:index'): (
                'posts/index.html'
            ),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'author'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': 1}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): (
                'posts/create_post.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': 1}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Список постов."""
        response = self.author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        self.assertEqual(post_text, 'Тестовый текст')
        self.assertEqual(post_author, PostURLTestPages.user)
        self.assertEqual(post_group, PostURLTestPages.group)

    def test_group_list(self):
        """Отфильтрованных по группе."""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))

        self.assertIn('page_obj', response.context)

        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа'
        )
        self.assertEqual(
            response.context.get('group').description, 'Тестовое описание')

        self.assertEqual(response.context.get('group').slug, 'test-slug')

    def test_profile(self):
        """отфильтрованных по пользователю."""
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'author'}
            )
        )
        post_object = response.context['page_obj'].object_list[0]
        self.assertEqual(post_object.text, 'Тестовый текст')
        self.assertEqual(str(post_object.group.title), 'Тестовая группа')
        self.assertEqual(post_object.group.title, 'Тестовая группа')
        self.assertEqual(str(post_object.author), 'author')

    def test_post_detail(self):
        """Один пост, отфильтрованный по id."""
        response = self.author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        objects = response.context['post'].id
        self.assertEqual(self.post.id, objects)

    def test_post_edit(self):
        """форма редактирования поста, отфильтрованного по id."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post(self):
        """форма создания поста."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post(self):
        """index, group_list, profile."""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'author'}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Тестовый текст')
                self.assertEqual(str(post.author), 'author')
                self.assertEqual(str(post.group), 'Тестовая группа')

    def test_new_post_absence(self):
        """Проверьте, что этот пост не попал в группу,
        для которой не был предназначен.
        """
        response = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(response.context.get('page_obj')[0].group,
                            self.group_two)

    def test_cache(self):
        """Проверяем работу кеша"""
        response = self.author_client.get(
            reverse('posts:index')
        )
        resp_1 = response.content
        post_deleted = Post.objects.get(id=self.post.id)
        post_deleted.delete()
        response_anoth = self.author_client.get(
            reverse('posts:index')
        )
        resp_2 = response_anoth.content
        self.assertTrue(resp_1 == resp_2)


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.number_test = 13
        objs = [
            Post(
                text=f'Тестовая запись {i}',
                author=cls.user,
                group=cls.group
            )
            for i in range(TestPaginator.number_test)
        ]
        Post.objects.bulk_create(objs)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_of_paginator(self):
        """Проверям пагинатор."""
        number_three = self.number_test - settings.NUMBER_OF_PAGINATOR
        paginator_dict = {
            self.client.get(reverse('posts:index')):
            settings.NUMBER_OF_PAGINATOR,
            self.client.get(reverse('posts:index') + '?page=2'):
            number_three,
            self.client.get(reverse('posts:group_list',
                            kwargs={'slug': 'test-slug'})):
            settings.NUMBER_OF_PAGINATOR,
            self.client.get(reverse('posts:group_list',
                            kwargs={'slug': 'test-slug'}) + '?page=2'):
            number_three,
            self.authorized_client.get(reverse('posts:profile',
                                       kwargs={'username': 'author'})):
            settings.NUMBER_OF_PAGINATOR,
            self.authorized_client.get(reverse('posts:profile',
                                       kwargs={'username': 'author'})
                                       + '?page=2'):
            number_three
        }
        for address, ciferka in paginator_dict.items():
            with self.subTest(address=address):
                self.assertEqual(len(address.context['page_obj']), ciferka)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestImageContext(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
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
        cache.clear()

    def test_context_image(self):
        """Проверяют, что при выводе поста с картинкой изображение передаётся
        в словаре context.
        """
        post_detail = self.authorized_client.get(reverse('posts:post_detail',
                                                         kwargs={'post_id': 1})
                                                 )
        self.assertEqual(post_detail.context['post'].image, self.post.image)
        url_dict = {
            reverse('posts:index'): (
                self.post.image
            ),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                self.post.image
            ),
            reverse('posts:profile', kwargs={'username': 'author'}): (
                self.post.image
            ),
        }
        for url, image in url_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'][0].image, image)


class TestFollowAndUnfollow(TestCase):
    def setUp(self):
        self.author = User.objects.create(username='author')
        self.user = User.objects.create(username='Larina')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_not_follow = User.objects.create(username='Vitalina')
        self.authorized_client_not_follow = Client()
        self.authorized_client_not_follow.force_login(self.user_not_follow)

    def test__user_follow_author(self):
        """Проверяем подписки."""
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        self.assertRedirects(response, f'/profile/{self.author}/')
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test__user_unfollow_author(self):
        """Проверяем отписки."""
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author})
        )
        self.assertRedirects(response, f'/profile/{self.author}/')
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_new_post_see_only_follow(self):
        """Запись есть."""
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        post = Post.objects.create(
            text='Test text',
            author=self.author
        )
        response_auth = self.authorized_client.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertIn(post, response_auth)

        response_not_auth = self.authorized_client_not_follow.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertNotIn(post, response_not_auth)
