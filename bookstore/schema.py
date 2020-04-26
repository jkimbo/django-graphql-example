import asyncio
from asgiref.sync import async_to_sync

import graphene
from django.utils.functional import cached_property
from graphene_django.views import GraphQLView
from aiodataloader import DataLoader
from graphql import parse, validate
from graphql.execution import ExecutionResult

from bookstore import models


class BooksByAuthorLoader(DataLoader):
    async def batch_load_fn(self, author_ids):
        return [models.Book.objects.filter(authors__id=id).all() for id in author_ids]


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

    async def resolve_books(root: models.Author, info):
        return await info.context.books_by_author_loader.load(root.id)


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
        return GQLContext(request)

    def execute_graphql_request(
        self, request, data, query, variables, operation_name, show_graphiql=False
    ):
        if not query:
            if show_graphiql:
                return None
            raise HttpError(HttpResponseBadRequest("Must provide query string."))

        try:
            document = parse(query)
        except Exception as e:
            return ExecutionResult(errors=[e])

        if request.method.lower() == "get":
            operation_ast = get_operation_ast(document, operation_name)
            if operation_ast and operation_ast.operation != OperationType.QUERY:
                if show_graphiql:
                    return None

                raise HttpError(
                    HttpResponseNotAllowed(
                        ["POST"],
                        "Can only perform a {} operation from a POST request.".format(
                            operation_ast.operation.value
                        ),
                    )
                )

        validation_errors = validate(self.schema.graphql_schema, document)
        if validation_errors:
            return ExecutionResult(data=None, errors=validation_errors)

        execute = async_to_sync(self.schema.execute_async)
        response = execute(
            source=query,
            root_value=self.get_root_value(request),
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.get_context(request),
            middleware=self.get_middleware(request),
        )
        return response
