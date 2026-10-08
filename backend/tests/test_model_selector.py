import unittest

from app.services.model_selector import classify_task, select_models


class ModelSelectorTests(unittest.TestCase):
    def test_examples_map_to_expected_categories(self) -> None:
        examples = {
            "Write a JavaScript function for binary search.": "Coding",
            "What is photosynthesis?": "General Knowledge",
            "If A is greater than B and B is greater than C, which is greatest?": "Reasoning",
            "Write a short story about a student who builds an AI.": "Creative Writing",
        }
        for query, expected in examples.items():
            with self.subTest(query=query):
                self.assertEqual(classify_task(query), expected)

    def test_unmatched_query_defaults_to_general_knowledge(self) -> None:
        self.assertEqual(classify_task("Tell me something interesting."), "General Knowledge")

    def test_baseline_model_is_fixed_for_every_task(self) -> None:
        coding_model, _ = select_models("Coding", "baseline")
        reasoning_model, _ = select_models("Reasoning", "baseline")
        self.assertEqual(coding_model, reasoning_model)

    def test_proposed_model_selection_is_deterministic_by_task(self) -> None:
        first = select_models("Reasoning", "proposed")
        second = select_models("Reasoning", "proposed")
        self.assertEqual(first, second)
        self.assertNotEqual(
            select_models("Coding", "proposed")[0],
            select_models("Reasoning", "proposed")[0],
        )


if __name__ == "__main__":
    unittest.main()
