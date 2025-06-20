# auth_app/serializers.py

from rest_framework import serializers
from .models import Survey, Question, Choice, Student, SurveyResponse


class ChoiceWithCountSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField()

    class Meta:
        model = Choice
        fields = ['id', 'text', 'count']


class QuestionStatisticsSerializer(serializers.ModelSerializer):
    choices_stats = ChoiceWithCountSerializer(many=True, read_only=True)
    text_answers = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        required=False
    )

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'choices_stats', 'text_answers']


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'is_required', 'choices']


class SurveyListSerializer(serializers.ModelSerializer):
    has_responded = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = ['id', 'title', 'description', 'is_anonymous', 'has_responded']

    def get_has_responded(self, obj):
        student = self.context['request'].current_student
        if not student or obj.is_anonymous:
            return False
        return SurveyResponse.objects.filter(survey=obj, student=student).exists()


class SurveyDetailSerializer(SurveyListSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(SurveyListSerializer.Meta):
        fields = SurveyListSerializer.Meta.fields + ['questions']


class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    text_answer = serializers.CharField(required=False, allow_blank=True)
    selected_choice_id = serializers.IntegerField(required=False, allow_null=True)
    selected_choices_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )

    def validate_question_id(self, value):
        if not Question.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bunday IDga ega savol mavjud emas.")
        return value


class SurveySubmitSerializer(serializers.Serializer):
    answers = AnswerSubmitSerializer(many=True)