from pathlib import Path
import unittest

from pydantic import ValidationError

from domain_models import CardDefinition, CardType, SessionDocument


EXAMPLE_PATH = Path(__file__).parents[1] / "examples" / "first_case_session.json"


class SessionDocumentTests(unittest.TestCase):
    def test_card_type_has_exactly_five_categories(self) -> None:
        self.assertEqual(
            {item.value for item in CardType},
            {"control_object", "property", "status", "link", "scene"},
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

    def test_attribute_helper_does_not_fill_status_cards(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        helper = next(
            value
            for value in session.current_draft.snapshot.card_field_values
            if value.purpose == "auxiliary"
        )
        resultant_reference = next(
            reference
            for reference in session.current_draft.snapshot.property_card_values[
                0
            ].status_card_references
            if reference.role == "resultant"
        )
        resultant = next(
            value
            for value in session.current_draft.snapshot.status_card_values
            if value.status_card_id == resultant_reference.status_card_id
        )

        self.assertNotEqual(helper.supplemental_text, resultant.selected_option_id)

    def test_property_card_lists_its_status_card_references(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        property_value = session.current_draft.snapshot.property_card_values[0]

        self.assertEqual(property_value.status_list_id, "motion-state-list")
        self.assertEqual(
            {reference.role for reference in property_value.status_card_references},
            {"tendency", "resultant"},
        )

    def test_status_card_must_reference_an_option_in_its_status_list(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["current_draft"]["snapshot"]["status_card_values"][0][
            "selected_option_id"
        ] = "unknown-option"

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_status_card_cannot_belong_to_two_property_cards(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        duplicated_property = dict(
            payload["current_draft"]["snapshot"]["property_card_values"][0]
        )
        payload["current_draft"]["snapshot"]["property_card_values"].append(
            duplicated_property
        )

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_duplicate_card_identity_is_rejected(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["registered_cards"].append(payload["registered_cards"][0])

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_non_null_marker_id_must_be_unique(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["registered_cards"][0]["marker_id"] = 101
        payload["registered_cards"][1]["marker_id"] = 101

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_card_definition_does_not_fix_a_control_object_role(self) -> None:
        with self.assertRaises(ValidationError):
            CardDefinition.model_validate(
                {
                    "card_id": "control-object-card",
                    "card_type": "control_object",
                    "control_object_role": "object",
                    "marker_id": None,
                }
            )

    def test_each_active_control_object_card_requires_one_role(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        payload["current_draft"]["snapshot"]["control_object_card_values"].pop()

        with self.assertRaises(ValidationError):
            SessionDocument.model_validate(payload)

    def test_a_control_object_card_can_change_role_between_explanations(self) -> None:
        session = SessionDocument.model_validate_json(EXAMPLE_PATH.read_text())
        payload = session.model_dump(mode="json")
        version_role = payload["explanation_versions"][0]["snapshot"][
            "control_object_card_values"
        ][0]
        version_role["role"] = "control"

        restored = SessionDocument.model_validate(payload)
        self.assertEqual(
            restored.current_draft.snapshot.control_object_card_values[0].role,
            "object",
        )
        self.assertEqual(
            restored.explanation_versions[0]
            .snapshot.control_object_card_values[0]
            .role,
            "control",
        )


if __name__ == "__main__":
    unittest.main()
