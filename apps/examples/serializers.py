"""
Serializers for Examples app.
"""
from rest_framework import serializers

from .models import Example


class ExampleSerializer(serializers.ModelSerializer):
    """Serializer for Example model."""

    class Meta:
        model = Example
        fields = [
            'id',
            'content',
            'mean',
            'trans',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
