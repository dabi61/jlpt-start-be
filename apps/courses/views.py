"""
Views for Courses app.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiTypes


class CoursePlaceholderView(APIView):
    """
    Temporary endpoint while the courses module is being implemented.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            501: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request):
        return Response(
            {
                'message': 'Courses module is not implemented yet.',
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
