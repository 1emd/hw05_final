from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from yatube.settings import POSTS_PER_PAGE


def get_page(request, post_list):
    return Paginator(post_list, POSTS_PER_PAGE).get_page(
        request.GET.get('page'))


@cache_page(20, key_prefix='index_page')
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': get_page(
            request, Post.objects.select_related('author', 'group').all())
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_page(request, group.posts.select_related(
            'author', 'group').all())
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': get_page(request, author.posts.all()),
        'following': (
            request.user != author
            and request.user.is_authenticated
            and Follow.objects.filter(
                author=author,
                user=request.user
            ).exists())
    })


def post_detail(request, post_id):
    return render(
        request, 'posts/post_detail.html', {
            'post': get_object_or_404(
                Post.objects.select_related('author', 'group'), id=post_id),
            'form': CommentForm(),
        })


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {'form': form, }
    if not form.is_valid():
        return render(request, 'posts/post_create.html', context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/post_create.html', context)


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
    return render(request, 'posts/follow.html', {
        'page_obj': get_page(request, Post.objects.filter(
            author__following__user=request.user))
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username).delete()
    return redirect('posts:follow_index')
