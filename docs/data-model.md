# D03 核心数据模型与 JSON 结构

状态：第三版，待用户审阅。

数据版本：`0.3`。

范围：本文件展开程序实际读取的 JSON 结构。R01 属性列表、R02 情境输入字段和 R03 拼接规则尚未确认，因此 `field_id`、`option_id` 和 `port_id` 只作为引用位置，不在 D03 中定义正式取值。

## 1. 顶层结构

一次小组完成一个任务的数据保存为一个 `SessionDocument`：

```json
{
  "schema_version": "0.3",
  "session_id": "session-example-001",
  "group_id": "group-example",
  "task_id": "first-case-no-added-horizontal-action",
  "registered_cards": [],
  "scene_objects": [],
  "status_lists": [],
  "current_draft": {
    "updated_at": "2026-11-12T10:00:00+08:00",
    "snapshot": {
      "scene_object_names": [],
      "card_states": [],
      "bindings": [],
      "card_field_values": [],
      "property_card_values": [],
      "status_card_values": [],
      "connections": []
    }
  },
  "scenario_inputs": [],
  "explanation_versions": [],
  "animation_results": [],
  "animation_runs": [],
  "key_events": []
}
```

| 字段 | JSON 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `schema_version` | string | 是 | 当前固定为 `0.3` |
| `session_id` | string | 是 | 一次小组任务会话的稳定 ID |
| `group_id` | string | 是 | 小组 ID |
| `task_id` | string | 是 | 实验任务 ID |
| `registered_cards` | `CardDefinition[]` | 是 | 本会话可识别的实体卡登记项 |
| `scene_objects` | `SceneObject[]` | 是 | 动画中的人或物 |
| `status_lists` | `StatusListDefinition[]` | 是 | 本次任务使用的状态列表定义快照 |
| `current_draft` | `ExplanationDraft` | 是 | 当前可修改解释 |
| `scenario_inputs` | `ScenarioInput[]` | 是 | 各次实际动画输入 |
| `explanation_versions` | `ExplanationVersion[]` | 是 | 运行前预测和最终提交版本 |
| `animation_results` | `AnimationResult[]` | 是 | 系统计算的动画结果 |
| `animation_runs` | `AnimationRun[]` | 是 | 输入、预测版本和结果的对应关系 |
| `key_events` | `KeyEvent[]` | 是 | 少量关键节点记录 |

## 2. 卡牌登记：`CardDefinition`

“实体卡”是所有物理卡牌的统称，不是 `card_type` 的一个取值。`card_type` 只有五种：

```text
control_object  控物件卡
property        属性卡
status          物件归位卡（StatusCard）
link            联动卡
scene           场景卡
```

控物件卡示例：

```json
{
  "card_id": "card-control-object-a-1",
  "card_type": "control_object",
  "control_object_role": "object",
  "marker_id": 101
}
```

其他类型示例：

```json
{
  "card_id": "card-property-motion",
  "card_type": "property",
  "control_object_role": null,
  "marker_id": 201
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `card_id` | string | 是 | 每张实体卡的稳定身份 |
| `card_type` | enum string | 是 | 只能是上述五种类型 |
| `control_object_role` | `"control" \| "object" \| null` | 条件必填 | 控物件卡必须填写；其他卡必须为 `null` 或省略 |
| `marker_id` | integer 或 null | 否 | 摄像头识别标记；鼠标模拟阶段可为空 |

`control_object_role` 是控物件卡自身的属性，不是属性卡。它区分同一种控物件卡当前被定义为控件还是物件。

## 3. 场景对象：`SceneObject`

```json
{
  "scene_object_id": "scene-object-a",
  "display_name": "物体A",
  "scene_asset_id": "slider-a"
}
```

| 字段 | JSON 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `scene_object_id` | string | 是 | 对象稳定身份，不随改名变化 |
| `display_name` | string | 是 | 所有绑定该对象的控物件卡共享的当前名称 |
| `scene_asset_id` | string | 是 | 动画中对应的人物或物体资源 |

控物件卡身份和场景对象身份必须分开。两张控物件卡可以通过两条 `CardBinding` 指向同一个 `scene_object_id`。

## 4. 卡牌位置：`CardState` 与 `CardPose`

```json
{
  "card_id": "card-control-object-a-1",
  "is_in_explanation": true,
  "pose": {
    "center": {"x": 0.22, "y": 0.55},
    "rotation_degrees": 0,
    "input_source": "mouse_simulation"
  }
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `card_id` | string | 是 | 引用 `registered_cards[].card_id` |
| `is_in_explanation` | boolean | 是 | `false` 表示移出当前解释，但可保留填写内容 |
| `pose.center.x/y` | number | 是 | 卡牌中心在操作区的归一化坐标，范围 `0–1` |
| `pose.rotation_degrees` | number | 是 | 几何朝向；不会改变卡牌内容含义 |
| `pose.input_source` | enum string | 是 | `mouse_simulation` 或 `camera` |

## 5. 对象绑定：`CardBinding`

```json
{
  "card_id": "card-control-object-a-1",
  "scene_object_id": "scene-object-a"
}
```

只有 `card_type = "control_object"` 的卡可以建立对象绑定。`card_id` 和 `scene_object_id` 都是引用，不复制对象名称；因此场景对象改名后，所有当前绑定卡可以同步显示新名称。

## 6. 普通填写内容：`CardFieldValue`

```json
{
  "card_id": "card-property-motion",
  "field_id": "property-helper",
  "purpose": "auxiliary",
  "selected_option_ids": [],
  "supplemental_text": "属性卡辅助信息"
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `card_id` | string | 是 | 内容所属实体卡 |
| `field_id` | string | 是 | 字段定义 ID；具体清单由后续规则确定 |
| `purpose` | `"explanation" \| "auxiliary"` | 是 | 区分结构化解释和属性卡辅助信息 |
| `selected_option_ids` | string[] | 是 | 用户确认的结构化选项，可为空数组 |
| `supplemental_text` | string 或 null | 否 | 自由文字，保存但不进入自动判定 |

实际动画条件不放在 `CardFieldValue` 中，而单独保存在 `ScenarioInput`，从数据结构上防止辅助信息或预测覆盖动画输入。

## 7. 状态列表：`StatusListDefinition`

状态列表是某个属性允许引用的状态选项目录。它不是用户解释草稿，而是任务定义的一部分；会话保存一份列表快照，保证列表以后修改时，旧版本仍能按原选项解释。

```json
{
  "status_list_id": "motion-state-list",
  "property_id": "motion-state",
  "label": "运动状态",
  "version": 1,
  "options": [
    {
      "option_id": "motion-state.uniform-rightward",
      "label": "示例占位：向右匀速"
    }
  ]
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `status_list_id` | string | 是 | 状态列表稳定 ID |
| `property_id` | string | 是 | 该列表服务的属性 |
| `label` | string | 是 | 列表显示名称 |
| `version` | integer | 是 | 列表版本，从 `1` 开始 |
| `options` | `StatusOption[]` | 是 | 按显示顺序保存状态选项 |
| `options[].option_id` | string | 是 | 列表内唯一的状态选项 ID |
| `options[].label` | string | 是 | 用户看到的选项文字 |

R01 尚未确认完整选项，因此示例里的选项只用于验证引用结构，不是最终状态列表。

## 8. 属性卡内容与关联：`PropertyCardValue`

属性卡明确保存自己关联的状态列表，以及关联的物件归位卡（StatusCard）：

```json
{
  "property_card_id": "card-property-motion",
  "property_id": "motion-state",
  "status_list_id": "motion-state-list",
  "status_card_references": [
    {
      "status_card_id": "card-status-tendency",
      "role": "tendency"
    },
    {
      "status_card_id": "card-status-resultant",
      "role": "resultant"
    }
  ]
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `property_card_id` | string | 是 | 必须引用属性卡 |
| `property_id` | string | 是 | 属性定义 ID，必须与状态列表的 `property_id` 一致 |
| `status_list_id` | string | 是 | 引用顶层 `status_lists` 中的列表 |
| `status_card_references` | `StatusCardReference[]` | 是 | 属性卡直接列出关联的 StatusCard，可为空数组 |
| `status_card_id` | string | 是 | 必须引用物件归位卡／StatusCard |
| `role` | `"tendency" \| "resultant"` | 是 | 该 StatusCard 在当前属性解释中的角色 |

这里是“属性卡关联哪些 StatusCard”的唯一来源；不再把 `property_card_id` 反向藏在 StatusCard 内容中，避免双向字段不一致。

## 9. 物件归位卡内容：`StatusCardValue`

英文统一使用 `StatusCard`，中文界面和研究材料继续称“物件归位卡”。StatusCard 表示对某个状态列表选项的引用：

```json
{
  "status_card_id": "card-status-resultant",
  "status_list_id": "motion-state-list",
  "selected_option_id": "motion-state.uniform-rightward",
  "supplemental_text": null
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `status_card_id` | string | 是 | 必须引用物件归位卡／StatusCard |
| `status_list_id` | string | 是 | 声明它引用哪个状态列表 |
| `selected_option_id` | string 或 null | 是 | 必须来自该列表的 `options`；草稿未填写时可为 `null` |
| `supplemental_text` | string 或 null | 否 | 自由文字，不判定正确性 |

StatusCard 的 Tendency／Resultant 角色保存在属性卡的 `status_card_references` 中；StatusCard 自身只负责引用列表及其选项。属性卡辅助信息不能自动生成或改写 `selected_option_id`。

## 10. 卡牌连接：`CardConnection`

```json
{
  "connection_id": "connection-object-property",
  "endpoint_a": {
    "card_id": "card-control-object-a-1",
    "port_id": "right"
  },
  "endpoint_b": {
    "card_id": "card-property-motion",
    "port_id": "left"
  }
}
```

`endpoint_a` 和 `endpoint_b` 都由 `card_id + port_id` 组成。这里只保存已经稳定建立的连接；靠近和候选连接不保存。哪些端口可以相连、连接是否具有语义方向，由 R03 决定，示例中的 `left/right` 不是最终端口表。

## 11. 完整解释快照：`ExplanationSnapshot`

```json
{
  "scene_object_names": [
    {"scene_object_id": "scene-object-a", "display_name": "物体A"}
  ],
  "card_states": [],
  "bindings": [],
  "card_field_values": [],
  "property_card_values": [],
  "status_card_values": [],
  "connections": []
}
```

| 字段 | 元素类型 | 作用 |
| --- | --- | --- |
| `scene_object_names` | `SceneObjectNameSnapshot[]` | 冻结保存当时的对象名称，后续改名不改写历史 |
| `card_states` | `CardState[]` | 保存当时参与解释的卡牌和位置 |
| `bindings` | `CardBinding[]` | 保存当时的对象绑定 |
| `card_field_values` | `CardFieldValue[]` | 保存已确认的普通填写内容 |
| `property_card_values` | `PropertyCardValue[]` | 保存属性、状态列表和关联 StatusCard |
| `status_card_values` | `StatusCardValue[]` | 保存各 StatusCard 引用的状态选项 |
| `connections` | `CardConnection[]` | 保存稳定连接结构 |

当前草稿与历史版本共用这一结构。区别是草稿可更新，而历史版本创建后不可修改。

## 12. 当前草稿：`ExplanationDraft`

```json
{
  "updated_at": "2026-11-12T10:02:00+08:00",
  "snapshot": {
    "scene_object_names": [],
    "card_states": [],
    "bindings": [],
    "card_field_values": [],
    "property_card_values": [],
    "status_card_values": [],
    "connections": []
  }
}
```

只有用户确认的编辑、稳定连接和稳定断开才能更新草稿。编辑面板中尚未确认的输入不进入该 JSON。

## 13. 动画实际输入：`ScenarioInput`

```json
{
  "input_id": "input-001",
  "scenario_id": "first-case-no-added-horizontal-action",
  "created_at": "2026-11-12T10:00:00+08:00",
  "conditions": [
    {
      "condition_id": "given-initial-motion",
      "origin": "system_given",
      "target_scene_object_id": "scene-object-a",
      "source_card_id": null,
      "field_id": "initial-horizontal-motion",
      "selected_option_id": "uniform-rightward"
    }
  ]
}
```

| 字段 | JSON 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `input_id` | string | 是 | 一组实际输入的稳定 ID |
| `scenario_id` | string | 是 | 对应有限场景定义 |
| `created_at` | ISO 8601 string | 是 | 输入保存时间 |
| `conditions` | `ScenarioCondition[]` | 是 | 系统给定或用户设置的条件 |
| `condition_id` | string | 是 | 单条条件 ID |
| `origin` | `"system_given" \| "user_set"` | 是 | 条件来源 |
| `target_scene_object_id` | string 或 null | 否 | 条件所指向的场景对象 |
| `source_card_id` | string 或 null | 条件必填 | 用户设置条件时必须引用已登记并已绑定的控物件卡；系统给定时可为空 |
| `field_id` | string | 是 | 输入字段定义 ID，由 R02 确定 |
| `selected_option_id` | string | 是 | 实际输入值，由 R02 确定 |

## 14. 解释版本：`ExplanationVersion`

```json
{
  "version_id": "version-prediction-001",
  "kind": "prediction",
  "created_at": "2026-11-12T10:02:00+08:00",
  "scenario_input_id": "input-001",
  "snapshot": {
    "scene_object_names": [],
    "card_states": [],
    "bindings": [],
    "card_field_values": [],
    "property_card_values": [],
    "status_card_values": [],
    "connections": []
  }
}
```

`kind` 只能是 `prediction` 或 `final_submission`。每次点击“开始”前新增预测版本，最终提交时新增最终版本。版本引用对应的 `scenario_input_id`，但不能修改那份输入。

## 15. 动画结果与运行对应

`AnimationResult`：

```json
{
  "result_id": "result-001",
  "created_at": "2026-11-12T10:02:05+08:00",
  "values": [
    {
      "scene_object_id": "scene-object-a",
      "property_id": "horizontal-motion",
      "option_id": "uniform-rightward"
    }
  ]
}
```

`AnimationRun`：

```json
{
  "run_id": "run-001",
  "scenario_input_id": "input-001",
  "prediction_version_id": "version-prediction-001",
  "result_id": "result-001",
  "started_at": "2026-11-12T10:02:01+08:00",
  "finished_at": "2026-11-12T10:02:05+08:00"
}
```

运行记录只建立三者的引用关系：

```text
ScenarioInput ──驱动──> AnimationResult
       │
       └──对应──> ExplanationVersion（用户预测）
```

修改用户预测不会改变同一 `ScenarioInput` 对应的物理动画结果。

## 16. 关键节点：`KeyEvent`

```json
{
  "event_id": "event-001",
  "kind": "prediction_saved",
  "occurred_at": "2026-11-12T10:02:00+08:00",
  "related_version_id": "version-prediction-001",
  "related_run_id": "run-001",
  "note": null
}
```

`kind` 第一版只有：

- `prediction_saved`
- `final_submitted`
- `system_interrupted`

不记录每次移动、点击、编辑和连接变化。

## 17. 当前程序校验的引用规则

- 所有 ID 在各自集合内必须唯一。
- 控物件卡必须填写 `control_object_role`；其他卡不得填写。
- 只有控物件卡可以绑定场景对象。
- 状态列表 ID 和每个列表内的选项 ID 必须唯一。
- 属性卡必须直接列出关联的 StatusCard，并引用与属性一致的状态列表。
- StatusCard 必须由一个属性卡关联，且只能关联一个属性卡。
- StatusCard 的选项必须存在于它所引用的状态列表中。
- 用户设置的情境条件必须引用已登记的来源卡。
- 解释版本必须引用已存在的情境输入。
- 动画运行必须引用预测版本，不能引用最终提交版本。
- 动画结果中的对象必须存在。
- 关键节点只能引用已存在的版本和运行。
- JSON 中出现模型未声明的额外字段会校验失败，避免悄悄保存未知含义。

## 18. 尚未由 D03 决定的取值

- 属性列表以及 Tendency／Resultant 的最终选项。
- 用户设置方向、大小等情境输入时的正式 `field_id` 与 `option_id`。
- 正式端口名称、合法连接矩阵和语义方向。
- 有限案例的正确性检查规则。

完整可运行示例见 [first_case_session.json](../backend/examples/first_case_session.json)。它用于验证结构保存和引用关系，不等于最终教学选项表。

```bash
cd backend
uv run python -m unittest discover -s tests
```
