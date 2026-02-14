"""
Views for Courses app.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CoursePlaceholderView(APIView):
    """
    Temporary endpoint while the courses module is being implemented.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                'message': 'Courses module is not implemented yet.',
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
