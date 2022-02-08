from xml.etree.ElementTree import Comment
from django import forms
from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'group': ('Группа'),
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 10, 'cols': 40}),
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_text = {
            'text': 'Текст комментария',
        }
