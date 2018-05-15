"""
GraphQL schemas for the blockstore models.
"""
import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.debug import DjangoDebug


from .models import Tag, Unit, Pathway


class TagType(DjangoObjectType):
    """Tag graphql type"""
    class Meta:
        model = Tag


class UnitType(DjangoObjectType):
    """Unit graphql type"""
    class Meta:
        model = Unit


class PathwayType(DjangoObjectType):
    """Unit graphql type"""
    class Meta:
        model = Pathway


class Query(graphene.ObjectType):
    """GraphQL queries"""
    # For debugging raw sql, parameters, etc.
    debug = graphene.Field(DjangoDebug, name='__debug')

    tags = graphene.List(TagType)
    units = graphene.List(UnitType)
    unit = graphene.Field(UnitType, id=graphene.String())

    pathways = graphene.List(PathwayType)
    pathway = graphene.Field(PathwayType, id=graphene.String())

    def resolve_tags(self, args, context, info):
        return Tag.objects.all()

    def resolve_units(self, args, context, info):
        return Unit.objects.select_related('author').all()

    def resolve_unit(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Unit.objects.get(id=id)
        return None

    def resolve_pathways(self, args, context, info):
        return Pathway.objects.select_related('author').all()

    def resolve_pathway(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Pathway.objects.get(id=id)
        return None

schema = graphene.Schema(query=Query)
