# D03 核心数据模型

状态：第一版，待用户审阅。  
范围：只规定已经确认的数据边界；R01 属性列表、R02 卡牌输入字段和 R03 拼接规则仍使用外部标识符，不在 D03 中提前定案。

## 总体结构

```text
SessionDocument
├── registered_cards       实体卡身份与类型登记
├── scene_objects          场景对象身份与当前共享名称
├── current_draft          当前已确认的解释草稿
├── scenario_inputs        各轮实际动画输入
├── explanation_versions   “开始”前预测与最终提交快照
├── animation_results      系统按物理规则生成的结果
├── animation_runs         输入、预测版本与动画结果的对应关系
└── key_events             预测保存、最终提交、故障中断
```

`SessionDocument` 是按小组和任务保存、恢复及导出的完整单元。当前草稿可以更新；解释版本、已使用的情境输入和动画结果一经保存便视为历史记录，后续操作只能新增记录，不能回写旧记录。

## 关键对象

| 数据对象 | 保存内容 | 明确不承担的职责 |
| --- | --- | --- |
| `CardDefinition` | 实体卡稳定 ID、六种既有类型之一、可选识别标记 | 不保存场景对象身份 |
| `SceneObject` | 场景对象稳定 ID、共享名称、场景资源 ID | 不保存某张卡独有的名称 |
| `CardBinding` | 卡牌 ID → 场景对象 ID | 不等于卡牌接口连接 |
| `CardState` | 卡牌是否在当前解释中、位置、角度和输入来源 | 旋转不改变内容含义 |
| `CardFieldValue` | 已确认的结构化选择、补充文字及“解释／辅助”用途 | 不保存实际动画输入；自由文字不判分 |
| `ReturnCardValue` | 物件归位卡引用的属性卡、Tendency／Resultant 角色和用户所选条目 | 不从属性卡辅助信息自动生成 |
| `CardConnection` | 两个稳定连接端点 | 不保存靠近或候选连接；合法性由 R03 决定 |
| `ScenarioInput` | 系统给定和用户设置的实际条件 | 不读取用户预测作为输入 |
| `ExplanationVersion` | 预测或最终提交时的完整解释快照及对应输入 ID | 保存后不可被草稿更新覆盖 |
| `AnimationResult` | 系统按实际输入算出的结果字段 | 不等于用户填写的 Resultant |

## 解释快照

当前草稿和每个解释版本使用同一种 `ExplanationSnapshot`：

- `scene_object_names`：保存当时的对象名称，保证以后重命名不会改写历史显示。
- `card_states`：当时参与解释的卡牌及位置。
- `bindings`：多张物件卡／控件卡可以同时绑定同一个场景对象。
- `card_field_values`：只纳入已确认编辑；结构化选择与自由文字分开保存。
- `return_card_values`：物件归位卡由用户独立填写，并明确区分 Tendency 与 Resultant。
- `connections`：只保存已经稳定建立的合法连接。

## 三类容易混淆的数据

```text
ScenarioInput ──驱动──> AnimationResult
       │
       └──由 ID 关联──> ExplanationVersion（用户预测）
```

- 情境输入控制动画。
- 解释版本记录用户当时怎样预测和解释。
- 动画结果记录系统实际播放出的结果。
- 修改解释版本中的关系或 Resultant，不能改变同一个情境输入对应的动画结果。

## 尚未由 D03 决定的内容

- 属性列表与 Tendency／Resultant 的最终选项和值域。
- 用户设置拉力方向、大小等情境输入时所使用的具体字段。
- 卡牌端口名称、合法连接矩阵及语义方向。
- 有限案例的正确性检查规则。

示例中的 `field_id`、`option_id` 和 `port_id` 只是可替换引用；R01–R04 确认后才能成为正式规则。

## 验证示例

示例文件：[first_case_session.json](../backend/examples/first_case_session.json)。它表达“系统给定 A 向右匀速、无新增水平作用”的一次运行前预测及结果记录，目的是验证保存、载入和还原关系，不是最终教学选项表。

```bash
cd backend
uv run python -m unittest discover -s tests
```
