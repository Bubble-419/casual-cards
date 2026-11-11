from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CardType(StrEnum):
    OBJECT = "object"
    CONTROL = "control"
    PROPERTY = "property"
    RETURN = "return"
    LINK = "link"
    SCENE = "scene"


class InputSource(StrEnum):
    MOUSE_SIMULATION = "mouse_simulation"
    CAMERA = "camera"


class FieldPurpose(StrEnum):
    EXPLANATION = "explanation"
    AUXILIARY = "auxiliary"


class ReturnRole(StrEnum):
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


class CardFieldValue(DomainModel):
    card_id: str
    field_id: str
    purpose: FieldPurpose
    selected_option_ids: list[str] = Field(default_factory=list)
    supplemental_text: str | None = None


class ReturnCardValue(DomainModel):
    return_card_id: str
    property_card_id: str
    role: ReturnRole
    selected_option_id: str | None = None
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
    card_field_values: list[CardFieldValue]
    return_card_values: list[ReturnCardValue]
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
    schema_version: Literal["0.1"]
    session_id: str
    group_id: str
    task_id: str
    registered_cards: list[CardDefinition]
    scene_objects: list[SceneObject]
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
        self._require_unique("scene object", scene_object_id_values)
        self._require_unique("scenario input", [item.input_id for item in self.scenario_inputs])
        self._require_unique("explanation version", [item.version_id for item in self.explanation_versions])
        self._require_unique("animation result", [item.result_id for item in self.animation_results])
        self._require_unique("animation run", [item.run_id for item in self.animation_runs])

        card_types = {card.card_id: card.card_type for card in self.registered_cards}
        scene_object_ids = set(scene_object_id_values)
        scenario_input_ids = {item.input_id for item in self.scenario_inputs}
        version_kinds = {item.version_id: item.kind for item in self.explanation_versions}
        result_ids = {item.result_id for item in self.animation_results}
        run_ids = {item.run_id for item in self.animation_runs}

        snapshots = [self.current_draft.snapshot]
        snapshots.extend(version.snapshot for version in self.explanation_versions)
        for snapshot in snapshots:
            self._validate_snapshot(snapshot, card_types, scene_object_ids)

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
    def _require_unique(label: str, values: list[str]) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {label} id")

    @staticmethod
    def _validate_snapshot(
        snapshot: ExplanationSnapshot,
        card_types: dict[str, CardType],
        scene_object_ids: set[str],
    ) -> None:
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
            if card_types[binding.card_id] not in {CardType.OBJECT, CardType.CONTROL}:
                raise ValueError("only object and control cards can bind scene objects")
        for field_value in snapshot.card_field_values:
            if field_value.card_id not in card_types:
                raise ValueError("card field value references an unknown card")
        for return_value in snapshot.return_card_values:
            if card_types.get(return_value.return_card_id) is not CardType.RETURN:
                raise ValueError("return value requires a return card")
            if card_types.get(return_value.property_card_id) is not CardType.PROPERTY:
                raise ValueError("return value must reference a property card")
        for connection in snapshot.connections:
            if connection.endpoint_a.card_id not in card_types:
                raise ValueError("connection endpoint references an unknown card")
            if connection.endpoint_b.card_id not in card_types:
                raise ValueError("connection endpoint references an unknown card")
