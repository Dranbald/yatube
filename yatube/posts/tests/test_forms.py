import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from ..forms import PostForm
from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT + '/media/')
class PostCreatFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
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
        cls.group_get = get_object_or_404(Group, slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostCreatFormTests.user)

    def test_create_post(self):
        """Форма создающая запись в БД"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        post = Post.objects.all().order_by('-id')[0]
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text='Тестовая запись').exists())
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/' + uploaded.name)

    def test_form_image(self):
        empty_form = (b'')
        empty_field = SimpleUploadedFile(
            name='img.gif',
            content=empty_form,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.id,
            'image': empty_field,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            'image',
            'Отправленный файл пуст.'
        )

    def test_edit_post(self):
        """Проверка формы редактирования поста в БД"""
        posts_count = Post.objects.count()
        form_data_edit = {
            'text': 'Тестовая запись 2',
            'group': self.group.id
        }
        reverse_name = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        response = self.author_client.post(
            reverse_name,
            data=form_data_edit,
            follow=True
        )
        edit_post = response.context['post']
        self.assertEqual(edit_post.text, 'Тестовая запись 2')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))

    def test_form_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Добавленный тестовый комментарий',
            'author': self.user
        }
        url = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id})

        response = self.author_client.post(
            url,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

        comment = response.context['comments'].first()
        self.assertEqual(
            comment.text, form_data['text'], 'Неверный текст у комментария')
        self.assertEqual(
            comment.author.username,
            self.user.username,
            'Неверный автор у комментария')
        self.assertEqual(Comment.objects.count(), comment_count + 1)
