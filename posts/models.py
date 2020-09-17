from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=20, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name="posts"
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        part_text = self.text[0:100]
        author = self.author
        pub_date = self.pub_date
        return f'{part_text}, {author}, {pub_date}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name="comments")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="comments")
    text = models.TextField(max_length=1000)
    created = models.DateTimeField("date published", auto_now_add=True)

    class Meta:
        ordering = ("-created",)


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="following"
    )
