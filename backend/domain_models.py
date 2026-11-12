from __future__ import annotations

from collections.abc import Hashable, Sequence
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CardType(StrEnum):
    CONTROL_OBJECT = "control_object"
    PROPERTY = "property"
    STATUS = "status"
    LINK = "link"
    SCENE = "scene"


class ControlObjectRole(StrEnum):
    CONTROL = "control"
    OBJECT = "object"


class InputSource(StrEnum):
    MOUSE_SIMULATION = "mouse_simulation"
    CAMERA = "camera"


class FieldPurpose(StrEnum):
    EXPLANATION = "explanation"
    AUXILIARY = "auxiliary"


class StatusCardRole(StrEnum):
    TENDENCY = "tendency"
    RESULTANT = "resultant"


class ConditionOrigin(StrEnum):
    SYSTEM_GIVEN = "system_given"
    USER_SET = "user_set"


class VersionKind(StrEnum):
    PREDICTION = "prediction"
    FINAL_SUBMISSION = "final_submission"


class KeyEventKind(StrEnum):
    PREDICTION_SAVED = "prediction_saved"
    FINAL_SUBMITTED = "final_submitted"
    SYSTEM_INTERRUPTED = "system_interrupted"


class NormalizedPoint(DomainModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class CardPose(DomainModel):
    center: NormalizedPoint
    rotation_degrees: float
    input_source: InputSource


class CardDefinition(DomainModel):
    card_id: str
    card_type: CardType
    marker_id: int | None = Field(default=None, ge=0)


class SceneObject(DomainModel):
    scene_object_id: str
    display_name: str
    scene_asset_id: str


class StatusOption(DomainModel):
    option_id: str
    label: str


class StatusListDefinition(DomainModel):
    status_list_id: str
    property_id: str
    label: str
    version: int = Field(ge=1)
    options: list[StatusOption]


class CardState(DomainModel):
    card_id: str
    is_in_explanation: bool
    pose: CardPose


class SceneObjectNameSnapshot(DomainModel):
    scene_object_id: str
    display_name: str


class CardBinding(DomainModel):
    card_id: str
    scene_object_id: str


class ControlObjectCardValue(DomainModel):
    control_object_card_id: str
    role: ControlObjectRole


class CardFieldValue(DomainModel):
    card_id: str
    field_id: str
    purpose: FieldPurpose
    selected_option_ids: list[str]
    supplemental_text: str | None = None


class StatusCardReference(DomainModel):
    status_card_id: str
    role: StatusCardRole


class PropertyCardValue(DomainModel):
    property_card_id: str
    property_id: str
    status_list_id: str
    status_card_references: list[StatusCardReference]


class StatusCardValue(DomainModel):
    status_card_id: str
    status_list_id: str
    selected_option_id: str | None
    supplemental_text: str | None = None


class CardEndpoint(DomainModel):
    card_id: str
    port_id: str


class CardConnection(DomainModel):
    connection_id: str
    endpoint_a: CardEndpoint
    endpoint_b: CardEndpoint


class ExplanationSnapshot(DomainModel):
    scene_object_names: list[SceneObjectNameSnapshot]
    card_states: list[CardState]
    bindings: list[CardBinding]
    control_object_card_values: list[ControlObjectCardValue]
    card_field_values: list[CardFieldValue]
    property_card_values: list[PropertyCardValue]
    status_card_values: list[StatusCardValue]
    connections: list[CardConnection]


class ExplanationDraft(DomainModel):
    updated_at: datetime
    snapshot: ExplanationSnapshot


class ScenarioCondition(DomainModel):
    condition_id: str
    origin: ConditionOrigin
    target_scene_object_id: str | None = None
    source_card_id: str | None = None
    field_id: str
    selected_option_id: str


class ScenarioInput(DomainModel):
    input_id: str
    scenario_id: str
    created_at: datetime
    conditions: list[ScenarioCondition]


class ExplanationVersion(DomainModel):
    version_id: str
    kind: VersionKind
    created_at: datetime
    scenario_input_id: str
    snapshot: ExplanationSnapshot


class AnimationResultValue(DomainModel):
    scene_object_id: str
    property_id: str
    option_id: str


class AnimationResult(DomainModel):
    result_id: str
    created_at: datetime
    values: list[AnimationResultValue]


class AnimationRun(DomainModel):
    run_id: str
    scenario_input_id: str
    prediction_version_id: str
    result_id: str
    started_at: datetime
    finished_at: datetime


class KeyEvent(DomainModel):
    event_id: str
    kind: KeyEventKind
    occurred_at: datetime
    related_version_id: str | None = None
    related_run_id: str | None = None
    note: str | None = None


class SessionDocument(DomainModel):
    schema_version: Literal["0.4"]
    session_id: str
    group_id: str
    task_id: str
    registered_cards: list[CardDefinition]
    scene_objects: list[SceneObject]
    status_lists: list[StatusListDefinition]
    current_draft: ExplanationDraft
    scenario_inputs: list[ScenarioInput]
    explanation_versions: list[ExplanationVersion]
    animation_results: list[AnimationResult]
    animation_runs: list[AnimationRun]
    key_events: list[KeyEvent]

    @model_validator(mode="after")
    def validate_references(self) -> SessionDocument:
        card_ids = [card.card_id for card in self.registered_cards]
        scene_object_id_values = [item.scene_object_id for item in self.scene_objects]
        self._require_unique("registered card", card_ids)
        self._require_unique(
            "card marker",
            [
                card.marker_id
                for card in self.registered_cards
                if card.marker_id is not None
            ],
        )
        self._require_unique("scene object", scene_object_id_values)
        self._require_unique("scenario input", [item.input_id for item in self.scenario_inputs])
        self._require_unique("explanation version", [item.version_id for item in self.explanation_versions])
        self._require_unique("animation result", [item.result_id for item in self.animation_results])
        self._require_unique("animation run", [item.run_id for item in self.animation_runs])
        self._require_unique("key event", [item.event_id for item in self.key_events])
        self._require_unique("status list", [item.status_list_id for item in self.status_lists])

        status_lists = {item.status_list_id: item for item in self.status_lists}
        for status_list in self.status_lists:
            self._require_unique(
                f"status option in {status_list.status_list_id}",
                [option.option_id for option in status_list.options],
            )

        card_types = {card.card_id: card.card_type for card in self.registered_cards}
        scene_object_ids = set(scene_object_id_values)
        scenario_inputs_by_id = {item.input_id: item for item in self.scenario_inputs}
        scenario_input_ids = set(scenario_inputs_by_id)
        version_kinds = {item.version_id: item.kind for item in self.explanation_versions}
        result_ids = {item.result_id for item in self.animation_results}
        run_ids = {item.run_id for item in self.animation_runs}

        snapshots = [self.current_draft.snapshot]
        snapshots.extend(version.snapshot for version in self.explanation_versions)
        for snapshot in snapshots:
            self._validate_snapshot(
                snapshot,
                card_types,
                scene_object_ids,
                status_lists,
            )

        for scenario_input in self.scenario_inputs:
            for condition in scenario_input.conditions:
                if (
                    condition.target_scene_object_id is not None
                    and condition.target_scene_object_id not in scene_object_ids
                ):
                    raise ValueError("scenario condition references an unknown scene object")
                if condition.origin is ConditionOrigin.USER_SET:
                    if condition.source_card_id not in card_types:
                        raise ValueError("user-set condition requires a registered source card")

        for version in self.explanation_versions:
            if version.scenario_input_id not in scenario_input_ids:
                raise ValueError("explanation version references an unknown scenario input")
            bound_card_ids = {binding.card_id for binding in version.snapshot.bindings}
            version_input = scenario_inputs_by_id[version.scenario_input_id]
            for condition in version_input.conditions:
                if (
                    condition.origin is ConditionOrigin.USER_SET
                    and condition.source_card_id not in bound_card_ids
                ):
                    raise ValueError(
                        "user-set condition source card must be bound in the explanation version"
                    )

        for result in self.animation_results:
            if any(value.scene_object_id not in scene_object_ids for value in result.values):
                raise ValueError("animation result references an unknown scene object")

        for run in self.animation_runs:
            if run.scenario_input_id not in scenario_input_ids:
                raise ValueError("animation run references an unknown scenario input")
            if run.prediction_version_id not in version_kinds:
                raise ValueError("animation run references an unknown prediction version")
            if version_kinds[run.prediction_version_id] is not VersionKind.PREDICTION:
                raise ValueError("animation run must reference a prediction version")
            if run.result_id not in result_ids:
                raise ValueError("animation run references an unknown animation result")

        for event in self.key_events:
            if (
                event.related_version_id is not None
                and event.related_version_id not in version_kinds
            ):
                raise ValueError("key event references an unknown explanation version")
            if event.related_run_id is not None and event.related_run_id not in run_ids:
                raise ValueError("key event references an unknown animation run")
        return self

    @staticmethod
    def _require_unique(label: str, values: Sequence[Hashable]) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {label} id")

    @staticmethod
    def _validate_snapshot(
        snapshot: ExplanationSnapshot,
        card_types: dict[str, CardType],
        scene_object_ids: set[str],
        status_lists: dict[str, StatusListDefinition],
    ) -> None:
        SessionDocument._require_unique(
            "card state", [state.card_id for state in snapshot.card_states]
        )
        SessionDocument._require_unique(
            "scene-object name", [name.scene_object_id for name in snapshot.scene_object_names]
        )
        SessionDocument._require_unique(
            "card binding", [binding.card_id for binding in snapshot.bindings]
        )
        SessionDocument._require_unique(
            "connection", [connection.connection_id for connection in snapshot.connections]
        )
        for card_state in snapshot.card_states:
            if card_state.card_id not in card_types:
                raise ValueError("snapshot references an unknown card")
        for name in snapshot.scene_object_names:
            if name.scene_object_id not in scene_object_ids:
                raise ValueError("snapshot name references an unknown scene object")
        for binding in snapshot.bindings:
            if binding.card_id not in card_types:
                raise ValueError("binding references an unknown card")
            if binding.scene_object_id not in scene_object_ids:
                raise ValueError("binding references an unknown scene object")
            if card_types[binding.card_id] is not CardType.CONTROL_OBJECT:
                raise ValueError("only control-object cards can bind scene objects")

        active_control_object_card_ids = {
            state.card_id
            for state in snapshot.card_states
            if state.is_in_explanation
            and card_types[state.card_id] is CardType.CONTROL_OBJECT
        }
        role_card_ids = [
            value.control_object_card_id
            for value in snapshot.control_object_card_values
        ]
        SessionDocument._require_unique("control-object card value", role_card_ids)
        for value in snapshot.control_object_card_values:
            if card_types.get(value.control_object_card_id) is not CardType.CONTROL_OBJECT:
                raise ValueError("control-object role requires a control-object card")
            if value.control_object_card_id not in active_control_object_card_ids:
                raise ValueError(
                    "control-object role requires a card in the explanation"
                )
        if set(role_card_ids) != active_control_object_card_ids:
            raise ValueError(
                "each control-object card in the explanation requires exactly one role"
            )
        for field_value in snapshot.card_field_values:
            if field_value.card_id not in card_types:
                raise ValueError("card field value references an unknown card")

        status_values = {
            value.status_card_id: value for value in snapshot.status_card_values
        }
        if len(status_values) != len(snapshot.status_card_values):
            raise ValueError("duplicate status card value")

        referenced_status_cards: dict[str, tuple[str, str]] = {}
        property_card_ids = [
            value.property_card_id for value in snapshot.property_card_values
        ]
        if len(property_card_ids) != len(set(property_card_ids)):
            raise ValueError("duplicate property card value")
        for property_value in snapshot.property_card_values:
            if card_types.get(property_value.property_card_id) is not CardType.PROPERTY:
                raise ValueError("property card value requires a property card")
            status_list = status_lists.get(property_value.status_list_id)
            if status_list is None:
                raise ValueError("property card value references an unknown status list")
            if status_list.property_id != property_value.property_id:
                raise ValueError("property card value does not match its status list property")
            for reference in property_value.status_card_references:
                if card_types.get(reference.status_card_id) is not CardType.STATUS:
                    raise ValueError("property card must reference a status card")
                if reference.status_card_id in referenced_status_cards:
                    raise ValueError("status card cannot belong to more than one property card")
                referenced_status_cards[reference.status_card_id] = (
                    property_value.property_card_id,
                    property_value.status_list_id,
                )

        for status_value in snapshot.status_card_values:
            if card_types.get(status_value.status_card_id) is not CardType.STATUS:
                raise ValueError("status value requires a status card")
            status_list = status_lists.get(status_value.status_list_id)
            if status_list is None:
                raise ValueError("status card value references an unknown status list")
            reference = referenced_status_cards.get(status_value.status_card_id)
            if reference is None:
                raise ValueError("status card value must be associated by a property card")
            if reference[1] != status_value.status_list_id:
                raise ValueError("status card and property card must use the same status list")
            if status_value.selected_option_id is not None:
                option_ids = {option.option_id for option in status_list.options}
                if status_value.selected_option_id not in option_ids:
                    raise ValueError("status card value references an unknown status option")

        if set(status_values) != set(referenced_status_cards):
            raise ValueError("each associated status card requires exactly one status value")
        for connection in snapshot.connections:
            if connection.endpoint_a.card_id not in card_types:
                raise ValueError("connection endpoint references an unknown card")
            if connection.endpoint_b.card_id not in card_types:
                raise ValueError("connection endpoint references an unknown card")
