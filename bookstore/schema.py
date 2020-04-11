import asyncio

import graphene
from django.utils.functional import cached_property
from graphene_django.views import GraphQLView
from promise import Promise
from promise.dataloader import DataLoader
from promise import set_default_scheduler
from promise.schedulers.thread import ThreadScheduler

from bookstore import models

set_default_scheduler(ThreadScheduler())

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class BooksByAuthorLoader(DataLoader):
    def batch_load_fn(self, author_ids):
        print(author_ids)
        return Promise.resolve([models.Book.objects.filter(authors__id=id).all() for id in author_ids])


class BookType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    authors = graphene.List('bookstore.schema.AuthorType')

    def resolve_authors(root: models.Book, info):
        return root.authors.all()


class AuthorType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    books = graphene.List(lambda: BookType)

    def resolve_books(root: models.Author, info, **kwargs):
        return info.context.books_by_author_loader.load(root.id)


class Query(graphene.ObjectType):
    author = graphene.Field(AuthorType, id=graphene.Int())
    authors = graphene.List(AuthorType)
    book = graphene.Field(BookType, id=graphene.Int())

    def resolve_author(root, info, id: int):
        return models.Author.objects.get(pk=id)

    def resolve_authors(root, info):
        return models.Author.objects.all()

    def resolve_book(root, info, id: int):
        return models.Author.objects.get(pk=id)


schema = graphene.Schema(query=Query)


class GQLContext:
    def __init__(self, request):
        self.request = request

    @cached_property
    def user(self):
        return self.request.user

    @cached_property
    def books_by_author_loader(self):
        return BooksByAuthorLoader()


class BookstoreGraphQLView(GraphQLView):
    def get_context(self, request):
        view_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(view_loop)
        return GQLContext(request)
