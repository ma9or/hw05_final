import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.views import NUM_POST

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='ght')
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
        uploaded1 = SimpleUploadedFile(
            name='lol_small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
            image=uploaded
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
            image=uploaded1
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug':
                            PostPagesTests.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            PostPagesTests.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            PostPagesTests.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            PostPagesTests.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        for post in Post.objects.all():
            self.assertIn(post, page_obj)
            first_object = response.context['page_obj'][0]
            posts_image_0 = first_object.image
            self.assertEqual(posts_image_0, PostPagesTests.post1.image)
            second_object = response.context['page_obj'][1]
            posts_image_1 = second_object.image
            self.assertEqual(posts_image_1, PostPagesTests.post.image)

    def test_cache_index_page_correct_context(self):
        """Кэш index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        post_id = PostPagesTests.post.id
        instance = Post.objects.get(pk=post_id)
        instance.delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        new_content = new_response.content
        self.assertEqual(content, new_content)
        cache.clear()
        new_new_response = self.authorized_client.get(reverse('posts:index'))
        new_new_content = new_new_response.content
        self.assertNotEqual(content, new_new_content)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        for post in Post.objects.all():
            response = self.authorized_client.get(reverse(
                                                  'posts:group_posts',
                                                  kwargs={'slug':
                                                          PostPagesTests.
                                                          group.slug}))
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)
            first_object = response.context['page_obj'][0]
            posts_image_0 = first_object.image
            self.assertEqual(posts_image_0, PostPagesTests.post1.image)
            second_object = response.context['page_obj'][1]
            posts_image_1 = second_object.image
            self.assertEqual(posts_image_1, PostPagesTests.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        for post in Post.objects.all():
            response = self.authorized_client.get(reverse(
                                                  'posts:profile',
                                                  kwargs={'username':
                                                          PostPagesTests.
                                                          user.username}))
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)
            first_object = response.context['page_obj'][0]
            posts_image_0 = first_object.image
            self.assertEqual(posts_image_0, PostPagesTests.post1.image)
            second_object = response.context['page_obj'][1]
            posts_image_1 = second_object.image
            self.assertEqual(posts_image_1, PostPagesTests.post.image)

    def test_posts_detail_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id':
                                                              PostPagesTests.
                                                              post.id}))
        post_context = response.context['post']
        self.assertEqual(post_context, PostPagesTests.post)
        first_object = response.context['post']
        posts_image = first_object.image
        self.assertEqual(posts_image, PostPagesTests.post.image)

    def test_create_post__page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        username_context = response.context['username']
        self.assertEqual(username_context, PostPagesTests.user)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              PostPagesTests.
                                                              post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        username_context = response.context['username']
        self.assertEqual(username_context, PostPagesTests.user)
        is_edit_context = response.context.get('is_edit')
        self.assertTrue(is_edit_context)

    def test_page_list_is_1(self):
        """Пост с группой попал на необходимые страницы."""
        field_urls_templates = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': PostPagesTests.group.slug}),
            reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username})
        ]
        for url in field_urls_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 2)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        author = self.user2
        user = self.user
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': author.username}
            )
        )
        self.assertTrue(Follow.objects.filter(author=author,
                                              user=user).exists())
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username':
                                             PostPagesTests.user2.username}))


class PaginatorViewsTest(TestCase):

    NUM_POST_OF_PAGE_TWO = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        list_objs = list()
        for i in range(NUM_POST + PaginatorViewsTest.NUM_POST_OF_PAGE_TWO):
            list_objs.append(Post.objects.create(
                author=cls.user,
                text=f'Тестовое содержание поста #{i}',
                group=cls.group)
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        cache.clear()

    def get_first_page_contains_ten_records(self, client, page_names):
        for url in page_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(len(response.context['page_obj']), NUM_POST)

    def get_second_page_contains_three_records(self, client, page_names):
        for url in page_names:
            with self.subTest(url=url):
                response = client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_paginator_pages(self):
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewsTest.
                            group.slug}),
            reverse('posts:profile', kwargs={'username':
                                             PaginatorViewsTest.
                                             user.username})
        ]
        self.get_first_page_contains_ten_records(self.authorized_client,
                                                 pages_names)
        self.get_second_page_contains_three_records(self.authorized_client,
                                                    pages_names)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='following')
        cls.visitor = User.objects.create_user(username='follower')
        cls.simple_user = User.objects.create_user(username='simpleUser')

    def setUp(self) -> None:
        self.visitor_client = Client()
        self.simple_user_client = Client()
        self.visitor_client.force_login(self.visitor)
        self.simple_user_client.force_login(self.simple_user)
        self.post = Post.objects.create(
            author=self.author,
            text='текст'
        )

    def test_user_can_following(self):
        """проверяем что можно подписаться"""
        follow_count = Follow.objects.count()
        self.visitor_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author.username,
        }))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_user_can_unfollowed(self):
        """проверяем что можно отписаться"""
        follow_count = Follow.objects.count()
        follow_count1 = follow_count + 1
        self.visitor_client.get(reverse('posts:profile_unfollow', kwargs={
            'username': self.author.username,
        }))
        self.assertEqual(Follow.objects.count(), follow_count1 - 1)

    def test_follow_page_for_follower(self):
        """Пост появляется на странице того, кто подписан"""
        self.visitor_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author.username,
        }))
        response = self.visitor_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        '''self.assertContains(response, self.post.text)'''

    def test_follow_page_for_user(self):
        """Пост не появляется на странице того, кто не подписан"""
        self.visitor_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author.username,
        }))
        response = self.simple_user_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post.text, response)
