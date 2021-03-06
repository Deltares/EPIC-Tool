import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from epic_app.models.epic_questions import (
    EvolutionQuestion,
    LinkagesQuestion,
    NationalFrameworkQuestion,
)
from epic_app.serializers.question_serializer import (
    EvolutionQuestionSerializer,
    LinkagesQuestionSerializer,
    NationalFrameworkQuestionSerializer,
)
from epic_app.tests.epic_db_fixture import epic_test_db


@pytest.fixture(autouse=True)
def question_serializer_fixture(
    epic_test_db: pytest.fixture,
):
    """
    Dummy fixture just to load a default db from dummy_db.

    Args:
        epic_test_db (pytest.fixture): Fixture to load for the whole file tests.
    """
    pass


def get_serializer():
    factory = APIRequestFactory()
    request = factory.get("/")

    return {
        "request": Request(request),
    }


serializer_context = get_serializer()


@pytest.mark.django_db
class TestNationalFrameworkSerializer:
    def test_given_valid_instances_when_to_representation_returns_expected_data(self):
        def validate_fields(dict_item: dict) -> bool:
            return "description" in list(dict_item.keys())

        serialized_data = list(
            NationalFrameworkQuestionSerializer(
                NationalFrameworkQuestion.objects.all(),
                many=True,
                context=serializer_context,
            ).data
        )

        assert len(serialized_data) == 2
        assert all(map(validate_fields, serialized_data))


@pytest.mark.django_db
class TestEvolutionQuestionSerializer:
    def test_given_valid_instances_when_to_representation_returns_expected_data(self):
        def validate_fields(dict_item: dict) -> bool:
            valid_fields = [
                "nascent_description",
                "engaged_description",
                "capable_description",
                "effective_description",
            ]
            return all(v_field in list(dict_item.keys()) for v_field in valid_fields)

        serialized_data = list(
            EvolutionQuestionSerializer(
                EvolutionQuestion.objects.all(), many=True, context=serializer_context
            ).data
        )

        assert len(serialized_data) == 2
        assert all(map(validate_fields, serialized_data))


@pytest.mark.django_db
class TestLinkagesQuestionSerializer:
    def test_given_valid_instances_when_to_representation_returns_expected_data(self):
        serialized_data = list(
            LinkagesQuestionSerializer(
                LinkagesQuestion.objects.all(), many=True, context=serializer_context
            ).data
        )

        assert len(serialized_data) == 1
