from linecache import cache
import shutil
import tempfile


from http import HTTPStatus
# from urllib import response
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..forms import PostForm
from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test',
            group=cls.group,
            image=uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        cache.clear()

    def test_create_post_authorized(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Тестовый текст',
            'image': PostCreateFormTests.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
                             'username': PostCreateFormTests.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group,
                text='test',
                author=PostCreateFormTests.user,
                image='posts/small.gif'
            ).exists()
        )

    def test_add_comment_authorized_client(self):
        """После проверки формы комментарий добавляется в пост"""
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data, follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
                             'post_id': PostCreateFormTests.post.id}))
        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий'
            ).exists())


class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Тестовая группа новая',
            slug='new-slug',
            description='Тестовое описание новой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое содержание поста',
            group=cls.group
        )
        cls.form = PostForm(instance=cls.post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostEditFormTests.user)
        cache.clear()

    def test_edit_post_authorized(self):
        """Тестируем редактирования поста авторизованным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'group': PostEditFormTests.new_group.id,
            'text': 'test',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostEditFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        modified_post = Post.objects.get(id=PostEditFormTests.post.id)
        self.assertEqual(modified_post.text, 'test')
        self.assertEqual(modified_post.group, PostEditFormTests.new_group)
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': PostEditFormTests.post.id}))
        self.assertFalse(
            Post.objects.filter(
                group=PostCreateFormTests.group,
                text='test',
                author=PostCreateFormTests.user
            ).exists()
        )
