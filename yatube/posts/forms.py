from xml.etree.ElementTree import Comment

from django import forms
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 10, 'cols': 40}),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_text = {
            'text': 'Текст комментария',
        }
