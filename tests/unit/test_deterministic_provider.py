from app.ai.providers.deterministic import NO_ANSWER, DeterministicGroundedProvider
from app.ai.types import RetrievedPassage


def test_deterministic_provider_quotes_the_passages_it_was_given() -> None:
    answer = DeterministicGroundedProvider().complete(
        question="What was revenue?",
        history=[],
        passages=[
            RetrievedPassage(document_title="Q3 finance note", content="Revenue was 10 million."),
        ],
    )
    assert "Q3 finance note" in answer
    assert "Revenue was 10 million." in answer
    assert answer.startswith("Based on the retrieved passages:")


def test_deterministic_provider_does_not_answer_without_passages() -> None:
    answer = DeterministicGroundedProvider().complete(
        question="What was revenue?",
        history=[],
        passages=[],
    )
    assert answer == NO_ANSWER
