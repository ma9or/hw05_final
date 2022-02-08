from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
# from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow

NUM_POST = 10

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, NUM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


def profile(request, username):
    """Список постов автора."""
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    count = author_posts.count()
    paginator = Paginator(author_posts, NUM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated and author != request.user:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    context = {
        'count': count,
        'author': author,
        'page_obj': page_obj,
        'following': following}
    return render(request, 'posts/profile.html', context)


@require_http_methods(["GET", "POST"])
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)

    context = {
        'form': form,
        'username': request.user,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    return render(request, 'posts/create_post.html',
                  {'form': form, 'username': request.user, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, NUM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Делает подписку на автора."""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author)
    if request.user != author and not follow.exists():
        Follow.objects.create(user=request.user,
                              author=author)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Делает отписку от автора."""
    author = User.objects.get(username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()
    return redirect('posts:profile', username=username)
