from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Follow, Group, Post, User

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


class TestStringMethods(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username="borya777")
        self.group = Group.objects.create(
            title="just_group",
            slug="just_group"
        )

    def test_create_profile(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_publication_authorize(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("new_post"),
            {"text": "ifre", "author": self.user.id, "group": self.group.id})
        self.assertEqual(
            (Post.objects.filter(
                text="ifre", author=self.user, group=self.group).count()), 1)

    def test_publication_non_authorize(self):
        response = self.client.get(reverse("new_post"), follow=True)
        self.assertRedirects(response, "/auth/login/?next=/new/")
        self.assertEqual(response.templates[0].name,
                         'registration/login.html')
        self.assertEqual(Post.objects.all().count(), 0)

    def response_pages(self):
        response_main = self.client.get(reverse("index"))
        response_profile = self.client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        response_post = self.client.get(
            reverse(
                "post", kwargs={
                    "username": self.user.username, "post_id": self.post.pk
                }
            )
        )
        response_group = self.client.get(
            reverse("group", kwargs={"slug": self.group.slug}))
        return [response_main,
                response_profile,
                response_post,
                response_group]

    def test_post_public(self):
        self.post = Post.objects.create(
            text="its free real estate",
            author=self.user,
            group=self.group)
        post_on_pages = self.response_pages()
        for post in post_on_pages:
            if "paginator" in post.context.keys():
                if post.context["paginator"].count == 1:
                    post = post.context["page"][0]
            else:
                post = post.context["post"]
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.user)
            self.assertEqual(post.group, self.group)
        self.assertEqual(Post.objects.all().count(), 1)

    def test_post_edit(self):
        self.post = Post.objects.create(
            text="its free real estate",
            author=self.user,
            group=self.group)
        self.group2 = Group.objects.create(
            title="just_group2",
            slug="just_group2"
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse(
                "post_edit", kwargs={
                    "username": self.user.username, "post_id": self.post.pk
                }
            ),
            {
                "text": "ifre",
                "author": self.user.id,
                "group": self.group2.id
            }
        )
        response_group = self.client.get(
            reverse(
                "group",
                kwargs={
                    "slug": self.group2.slug
                }
            )
        )
        posts_on_pages = self.response_pages()[:-1] + [response_group]
        for post in posts_on_pages:
            if "paginator" in post.context.keys():
                if post.context["paginator"].count == 1:
                    post = post.context["page"][0]
            else:
                post = post.context["post"]
            actual_post = Post.objects.get(pk=1)
            self.assertEqual(post.text, actual_post.text)
            self.assertEqual(post.author, self.user)
            self.assertEqual(post.group, actual_post.group)
        self.assertEqual(Post.objects.all().count(), 1)

    def test_page_404(self):
        response = self.client.get("/auth/auth/")
        self.assertEqual(response.status_code, 404)

    def test_image_on_post(self):
        img = SimpleUploadedFile(
            'small.gif',
            small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text="its free real estate",
            author=self.user,
            group=self.group,
            image=img
        )
        response = self.response_pages()[2]
        self.assertContains(response, text="<img")

    def test_image_on_pages(self):
        img = SimpleUploadedFile('small.gif', small_gif,
                                 content_type='image/gif')
        self.post = Post.objects.create(
            text="its free real estate",
            author=self.user,
            group=self.group,
            image=img
        )
        self.response_pages()
        post_pages = self.response_pages()[:-1]
        for post in post_pages:
            self.assertContains(post, text="<img")

    def test_upload_non_image(self):
        self.client.force_login(self.user)
        img = SimpleUploadedFile('small.txt', small_gif,
                                 content_type='text')
        response = self.client.post('/new/', {'text': 'test',
                                              'image': img,
                                              'group': self.group},
                                    follow=True)
        self.assertEqual(response.templates[0].name,
                         'posts/newpost.html')

    def test_cache_index(self):
        response_main_first = self.client.get(reverse("index"))
        self.post = Post.objects.create(
            text="its free real estate",
            author=self.user,
            group=self.group)
        response_main_second = self.client.get(reverse("index"))
        self.assertEqual(
            response_main_first.content,
            response_main_second.content
        )

    def following(self, follow_unfollow, author):
        self.client.post(
            reverse(
                follow_unfollow, kwargs={
                    "username": author.username
                }
            )
        )
        self.sub_count = Follow.objects.filter(
            user=self.user,
            author=author
        ).count()

    def test_following(self):
        self.client.force_login(self.user)
        author = User.objects.create_user(username="vanya666")
        self.following("profile_follow", author)
        self.assertEqual(self.sub_count, 1)
        self.following("profile_unfollow", author)
        self.assertEqual(self.sub_count, 0)

    def test_read_starred_authors(self):
        self.client.force_login(self.user)
        author = User.objects.create_user(username="vanya666")
        self.post = Post.objects.create(
            text="its free real estate",
            author=author
        )
        response = self.client.get(reverse("follow_index"))
        self.assertNotIn("post", response.context)
        self.following("profile_follow", author)
        response = self.client.get(reverse("follow_index"))
        self.assertIn("post", response.context)

    def test_comment_authorize(self):
        self.post = Post.objects.create(
            text="its free real estate",
            author=self.user,
            group=self.group)
        response_comment = self.client.post(
            reverse(
                "add_comment", kwargs={
                    "username": self.user.username, "post_id": self.post.pk
                }
            ),
            {
                "text": "just comment",
                "author": self.user.id,
                "post": self.post.pk
            }
        )
        self.assertEqual(response_comment.status_code, 302)
