"""
GraphQL schemas for the blockstore models.
"""
from graphene import relay, ObjectType, Schema, List
from graphene_django import DjangoObjectType
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField


from .models import Tag, Unit, Pathway


class TagNode(DjangoObjectType):
    """GraphQL Tag node"""
    class Meta:
        model = Tag
        filter_fields = ['name',]
        interfaces = (relay.Node, )


class UnitNode(DjangoObjectType):
    """GraphQL Unit node"""
    class Meta:
        model = Unit
        filter_fields = ['tags', 'author', ]
        interfaces = (relay.Node, )


class PathwayNode(DjangoObjectType):
    """GraphQL Pathway node"""
    tags = List(TagNode)

    class Meta:
        model = Pathway
        filter_fields = ['author', 'units',]
        interfaces = (relay.Node, )

    @staticmethod
    def resolve_tags(self, info, **kwargs):
        return self.tags


class Query(ObjectType):
    """GraphQL queries"""
    pathways = DjangoFilterConnectionField(PathwayNode)
    pathway = relay.Node.Field(PathwayNode)
    units = DjangoFilterConnectionField(UnitNode)
    unit = relay.Node.Field(UnitNode)
    tags = DjangoFilterConnectionField(TagNode)
    tag = relay.Node.Field(TagNode)


schema = Schema(query=Query)
