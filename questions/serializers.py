from rest_framework import serializers

class VoteSerializer(serializers.Serializer):
    vote = serializers.IntegerField(
        min_value=-1,
        max_value=1,
        required=True
    )