"""OAuth Source Serializer"""
from django.urls.base import reverse_lazy
from drf_yasg.utils import swagger_auto_schema, swagger_serializer_method
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.manager import MANAGER


class SourceTypeSerializer(PassiveSerializer):
    """Serializer for SourceType"""

    name = CharField(required=True)
    slug = CharField(required=True)
    urls_customizable = BooleanField()
    request_token_url = CharField(read_only=True, allow_null=True)
    authorization_url = CharField(read_only=True, allow_null=True)
    access_token_url = CharField(read_only=True, allow_null=True)
    profile_url = CharField(read_only=True, allow_null=True)


class OAuthSourceSerializer(SourceSerializer):
    """OAuth Source Serializer"""

    callback_url = SerializerMethodField()

    def get_callback_url(self, instance: OAuthSource) -> str:
        """Get OAuth Callback URL"""
        relative_url = reverse_lazy(
            "authentik_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": instance.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    type = SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=SourceTypeSerializer)
    def get_type(self, instace: OAuthSource) -> SourceTypeSerializer:
        """Get source's type configuration"""
        return SourceTypeSerializer(instace.type).data

    class Meta:
        model = OAuthSource
        fields = SourceSerializer.Meta.fields + [
            "provider_type",
            "request_token_url",
            "authorization_url",
            "access_token_url",
            "profile_url",
            "consumer_key",
            "consumer_secret",
            "callback_url",
            "type",
        ]


class OAuthSourceViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = OAuthSource.objects.all()
    serializer_class = OAuthSourceSerializer
    lookup_field = "slug"

    @swagger_auto_schema(responses={200: SourceTypeSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def source_types(self, request: Request) -> Response:
        """Get all creatable source types"""
        data = []
        for source_type in MANAGER.get():
            data.append(SourceTypeSerializer(source_type).data)
        return Response(data)
