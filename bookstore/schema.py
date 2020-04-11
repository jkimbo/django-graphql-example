import graphene

from bookstore import models


class BookType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    authors = graphene.List('bookstore.schema.AuthorType')

    def resolve_authors(root: models.Book, info):
        return root.authors.all()


class AuthorType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    books = graphene.List(BookType)

    def resolve_books(root: models.Author, info):
        return root.books.all()


class Query(graphene.ObjectType):
    author = graphene.Field(AuthorType, id=graphene.Int())
    book = graphene.Field(BookType, id=graphene.Int())

    def resolve_author(root, info, id: int):
        return models.Author.objects.get(pk=id)

    def resolve_book(root, info, id: int):
        return models.Author.objects.get(pk=id)


schema = graphene.Schema(query=Query)
