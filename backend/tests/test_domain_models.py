from pathlib import Path
import unittest

from pydantic import ValidationError

from domain_models import CardDefinition, CardType, SessionDocument


EXAMPLE_PATH = Path(__file__).parents[1] / "examples" / "first_case_session.json"


class SessionDocumentTests(unittest.TestCase):
    def test_card_type_has_exactly_five_categories(self) -> None:
        self.assertEqual(
            {item.value for item in CardType},
            {"control_object", "property", "return", "link", "scene"},
        )

    def test_example_round_trips_without_losing_data(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        restored = SessionDocument.model_validate_json(session.model_dump_json())

        self.assertEqual(restored, session)
        self.assertEqual(len(restored.current_draft.snapshot.bindings), 2)
        self.assertEqual(
            restored.current_draft.snapshot.bindings[0].scene_object_id,
            restored.current_draft.snapshot.bindings[1].scene_object_id,
        )

    def test_prediction_cannot_be_used_as_an_animation_input(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["scenario_inputs"][0]["conditions"][0]["source_card_id"] = (
            "unknown-prediction-card"
        )
        payload["scenario_inputs"][0]["conditions"][0]["origin"] = "user_set"

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_user_set_input_requires_a_bound_source_card(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["scenario_inputs"][0]["conditions"][0]["source_card_id"] = (
            "card-property-motion"
        )
        payload["scenario_inputs"][0]["conditions"][0]["origin"] = "user_set"

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_attribute_helper_does_not_fill_return_cards(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        helper = next(
            value
            for value in session.current_draft.snapshot.card_field_values
            if value.purpose == "auxiliary"
        )
        resultant = next(
            value
            for value in session.current_draft.snapshot.return_card_values
            if value.role == "resultant"
        )

        self.assertNotEqual(helper.supplemental_text, resultant.selected_option_id)

    def test_duplicate_card_identity_is_rejected(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["registered_cards"].append(payload["registered_cards"][0])

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_control_object_card_requires_its_role_attribute(self) -> None:
        with self.assertRaises(ValidationError):
            CardDefinition.model_validate(
                {
                    "card_id": "card-a",
                    "card_type": "control_object",
                    "control_object_role": None,
                    "marker_id": None,
                }
            )

    def test_other_card_types_cannot_have_a_control_object_role(self) -> None:
        with self.assertRaises(ValidationError):
            CardDefinition.model_validate(
                {
                    "card_id": "property-card",
                    "card_type": "property",
                    "control_object_role": "object",
                    "marker_id": None,
                }
            )


if __name__ == "__main__":
    unittest.main()
