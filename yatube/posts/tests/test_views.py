from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Group, Post, Follow

User = get_user_model()


class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='John')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_test',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_2 = User.objects.create_user(username='Name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author_2)
        self.author_client = Client()
        self.author_client.force_login(PostPageTests.user)

    def test_pages_uses_correct_template(self):
        """Корректное открытие страниц."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'slug_test'}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'John'}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPageTests.post.pk}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPageTests.post.pk}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template, 'Опять сломал!')

    def test_index_pages_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, 'John')

    def test_group_list_correct_context(self):
        """Шаблон группы"""
        response = self.author_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'slug_test'}))
        first_object = response.context["group"]
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, 'Тестовая группа')
        self.assertEqual(group_slug_0, 'slug_test')

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug_test'}))
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        self.assertTrue(post_text_0, 'Тестовый текст')

    def test_create_post_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'John'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username, 'John')
        self.assertEqual(post_text_0, 'Тестовый пост')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='varded'),
            text='Тестовый пост №1')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='John_1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Проверка кеширования главной страницы"""
        first_update = self.authorized_client.get(reverse('posts:index'))
        post_cache = Post.objects.get(pk=1)
        post_cache.text = 'Тестовый пост №2'
        post_cache.save()
        second_update = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_update.content, second_update.content)
        cache.clear()
        third_update = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_update.content, third_update.content)


class FollowTests(TestCase):
    def setUp(self):
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовый пост'
        )
        self.client_auth_follower = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following = Client()
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """Проверка подписки на автора"""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Проверка функции, отписаться от автора"""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_follower_lent(self):
        """Новый пост автора, виден его подписчикам"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, 'Тестовый пост')
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response, 'Тестовый пост')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test_slug2',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

        cls.posts = []
        for i in range(1, 13):
            cls.posts.append(Post.objects.create(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group))

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка паджинатора 10 постов страница 1."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug2'}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}
                    )
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_last_page_contains_three_records(self):
        """Проверка паджинатора 3 поста страница 2."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug2'}),
            reverse('posts:profile',
                    kwargs={'username': 'auth'}
                    )
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
