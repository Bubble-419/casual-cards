import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react'
import './App.css'

type HealthState = {
  status: string
  opencvVersion: string
}

type CardTemplateKey =
  | 'control_object'
  | 'property'
  | 'status'
  | 'link'
  | 'multi_link'
  | 'scene'

type SimulatedCard = {
  id: string
  templateKey: CardTemplateKey
  label: string
  shortLabel: string
  size: 'regular' | 'tall'
  x: number
  y: number
  rotationDegrees: number
  isOnWorkspace: boolean
  inputSource: 'mouse_simulation'
}

type DragState = {
  cardId: string
  pointerId: number
  offsetX: number
  offsetY: number
}

const CARD_TEMPLATES: Record<
  CardTemplateKey,
  { label: string; shortLabel: string; prefix: string; size: 'regular' | 'tall' }
> = {
  control_object: {
    label: '控物件卡',
    shortLabel: '控物件',
    prefix: 'C',
    size: 'regular',
  },
  property: {
    label: '属性卡',
    shortLabel: '属性',
    prefix: 'P',
    size: 'regular',
  },
  status: {
    label: '物件归位卡',
    shortLabel: '归位',
    prefix: 'S',
    size: 'regular',
  },
  link: {
    label: '联动卡',
    shortLabel: '联动',
    prefix: 'L',
    size: 'regular',
  },
  multi_link: {
    label: '多变量联动卡',
    shortLabel: '多变量',
    prefix: 'L',
    size: 'tall',
  },
  scene: {
    label: '场景卡',
    shortLabel: '场景',
    prefix: 'E',
    size: 'regular',
  },
}

const INITIAL_CARDS: SimulatedCard[] = [
  {
    id: 'C001',
    templateKey: 'control_object',
    ...CARD_TEMPLATES.control_object,
    x: 0.18,
    y: 0.49,
    rotationDegrees: 0,
    isOnWorkspace: true,
    inputSource: 'mouse_simulation',
  },
  {
    id: 'P001',
    templateKey: 'property',
    ...CARD_TEMPLATES.property,
    x: 0.33,
    y: 0.49,
    rotationDegrees: 0,
    isOnWorkspace: true,
    inputSource: 'mouse_simulation',
  },
  {
    id: 'S001',
    templateKey: 'status',
    ...CARD_TEMPLATES.status,
    x: 0.48,
    y: 0.49,
    rotationDegrees: 0,
    isOnWorkspace: true,
    inputSource: 'mouse_simulation',
  },
  {
    id: 'L001',
    templateKey: 'multi_link',
    ...CARD_TEMPLATES.multi_link,
    x: 0.66,
    y: 0.5,
    rotationDegrees: 0,
    isOnWorkspace: true,
    inputSource: 'mouse_simulation',
  },
]

function StatusBadge({ health }: { health: HealthState | null }) {
  const connected = health?.status === 'ok'
  return (
    <div className={`status-badge ${connected ? 'is-online' : ''}`}>
      <span className="status-dot" />
      <span>{connected ? '本地服务已连接' : '正在连接本地服务'}</span>
      {health && <small>OpenCV {health.opencvVersion}</small>}
    </div>
  )
}

function SceneControls() {
  return (
    <nav className="panel-controls" aria-label="动画控制">
      <button type="button" className="primary">开始</button>
      <button type="button">暂停／继续</button>
      <button type="button">重新开始</button>
    </nav>
  )
}

function CardControls() {
  return (
    <nav className="panel-controls" aria-label="解释构建控制">
      <button type="button">构建完成</button>
      <button type="button">提交最终解释</button>
    </nav>
  )
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

// D04 PROTOTYPE — validates that mouse-driven cards keep a stable identity while
// position, orientation and workspace presence change independently in memory.
function CardWorkspace() {
  const workspaceRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef<DragState | null>(null)
  const [cards, setCards] = useState<SimulatedCard[]>(INITIAL_CARDS)
  const [selectedCardId, setSelectedCardId] = useState(INITIAL_CARDS[0].id)

  const selectedCard = useMemo(
    () => cards.find((card) => card.id === selectedCardId) ?? null,
    [cards, selectedCardId],
  )
  const pickedUpCards = cards.filter((card) => !card.isOnWorkspace)

  function nextCardId(prefix: string) {
    const usedNumbers = cards
      .filter((card) => card.id.startsWith(prefix))
      .map((card) => Number.parseInt(card.id.slice(prefix.length), 10))
      .filter(Number.isFinite)
    return `${prefix}${String(Math.max(0, ...usedNumbers) + 1).padStart(3, '0')}`
  }

  function createCard(templateKey: CardTemplateKey) {
    const template = CARD_TEMPLATES[templateKey]
    const id = nextCardId(template.prefix)
    const visibleCount = cards.filter((card) => card.isOnWorkspace).length
    const card: SimulatedCard = {
      id,
      templateKey,
      ...template,
      x: clamp(0.14 + (visibleCount % 6) * 0.13, 0.1, 0.88),
      y: visibleCount % 2 === 0 ? 0.42 : 0.6,
      rotationDegrees: 0,
      isOnWorkspace: true,
      inputSource: 'mouse_simulation',
    }
    setCards((current) => [...current, card])
    setSelectedCardId(id)
  }

  function updateCard(cardId: string, update: Partial<SimulatedCard>) {
    setCards((current) =>
      current.map((card) => (card.id === cardId ? { ...card, ...update } : card)),
    )
  }

  function startDrag(event: ReactPointerEvent<HTMLDivElement>, card: SimulatedCard) {
    if (event.button !== 0 || !workspaceRef.current) return
    const workspaceRect = workspaceRef.current.getBoundingClientRect()
    dragRef.current = {
      cardId: card.id,
      pointerId: event.pointerId,
      offsetX: event.clientX - (workspaceRect.left + card.x * workspaceRect.width),
      offsetY: event.clientY - (workspaceRect.top + card.y * workspaceRect.height),
    }
    event.currentTarget.setPointerCapture(event.pointerId)
    setSelectedCardId(card.id)
  }

  function moveCard(event: ReactPointerEvent<HTMLDivElement>, card: SimulatedCard) {
    const drag = dragRef.current
    const workspace = workspaceRef.current
    if (!drag || drag.cardId !== card.id || drag.pointerId !== event.pointerId || !workspace) {
      return
    }

    const workspaceRect = workspace.getBoundingClientRect()
    const cardRect = event.currentTarget.getBoundingClientRect()
    const halfWidth = Math.min(cardRect.width / 2, workspaceRect.width / 2)
    const halfHeight = Math.min(cardRect.height / 2, workspaceRect.height / 2)
    const nextX = clamp(
      event.clientX - workspaceRect.left - drag.offsetX,
      halfWidth,
      workspaceRect.width - halfWidth,
    )
    const nextY = clamp(
      event.clientY - workspaceRect.top - drag.offsetY,
      halfHeight,
      workspaceRect.height - halfHeight,
    )
    updateCard(card.id, {
      x: nextX / workspaceRect.width,
      y: nextY / workspaceRect.height,
    })
  }

  function finishDrag(event: ReactPointerEvent<HTMLDivElement>) {
    if (dragRef.current?.pointerId === event.pointerId) {
      dragRef.current = null
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  function rotateCard(card: SimulatedCard) {
    updateCard(card.id, {
      rotationDegrees: (card.rotationDegrees + 15) % 360,
    })
    setSelectedCardId(card.id)
  }

  function pickUpCard(card: SimulatedCard) {
    updateCard(card.id, { isOnWorkspace: false })
    setSelectedCardId(card.id)
  }

  function returnCard(card: SimulatedCard) {
    updateCard(card.id, { isOnWorkspace: true })
    setSelectedCardId(card.id)
  }

  return (
    <section className="workspace-panel panel-cards">
      <header>
        <div className="panel-heading">
          <span className="panel-index">02</span>
          <h2>卡牌操作区</h2>
          <p>拖动卡牌；旋转与拿起只改变当前状态，不改变卡牌身份</p>
        </div>
        <CardControls />
      </header>

      <div className="card-prototype-toolbar" aria-label="鼠标模拟卡牌工具">
        <strong>新建模拟卡</strong>
        {(Object.keys(CARD_TEMPLATES) as CardTemplateKey[]).map((templateKey) => (
          <button type="button" key={templateKey} onClick={() => createCard(templateKey)}>
            ＋{CARD_TEMPLATES[templateKey].label}
          </button>
        ))}
        <span className="toolbar-divider" />
        <strong>已拿起 {pickedUpCards.length}</strong>
        {pickedUpCards.map((card) => (
          <button type="button" key={card.id} onClick={() => returnCard(card)}>
            放回 {card.id}
          </button>
        ))}
      </div>

      <div className="card-prototype-body">
        <div className="card-stage" ref={workspaceRef}>
          {cards
            .filter((card) => card.isOnWorkspace)
            .map((card) => (
              <div
                className={`simulated-card card-${card.templateKey} size-${card.size} ${
                  selectedCardId === card.id ? 'is-selected' : ''
                }`}
                key={card.id}
                style={{
                  left: `${card.x * 100}%`,
                  top: `${card.y * 100}%`,
                  transform: `translate(-50%, -50%) rotate(${card.rotationDegrees}deg)`,
                }}
                onPointerDown={(event) => startDrag(event, card)}
                onPointerMove={(event) => moveCard(event, card)}
                onPointerUp={finishDrag}
                onPointerCancel={finishDrag}
              >
                <div className="simulated-card-topline">
                  <span>{card.shortLabel}</span>
                  <code>{card.id}</code>
                </div>
                <div className="simulated-card-window">
                  <strong>{card.label}</strong>
                  <small>可编辑区域</small>
                </div>
                <div className="simulated-card-actions">
                  <button
                    type="button"
                    title="顺时针旋转 15°"
                    aria-label={`旋转 ${card.id}`}
                    onPointerDown={(event) => event.stopPropagation()}
                    onClick={() => rotateCard(card)}
                  >
                    ↻
                  </button>
                  <button
                    type="button"
                    title="从操作区拿起"
                    aria-label={`拿起 ${card.id}`}
                    onPointerDown={(event) => event.stopPropagation()}
                    onClick={() => pickUpCard(card)}
                  >
                    ↑
                  </button>
                </div>
              </div>
            ))}
          <div className="stage-hint">按住卡牌拖动 · 卡内 ↻ 旋转 · ↑ 拿起</div>
        </div>

        <aside className="card-state-inspector" aria-live="polite">
          <span className="inspector-kicker">当前卡牌状态</span>
          {selectedCard ? (
            <dl>
              <div><dt>原型 card_id</dt><dd>{selectedCard.id}</dd></div>
              <div><dt>类型</dt><dd>{selectedCard.label}</dd></div>
              <div><dt>位置 x</dt><dd>{selectedCard.x.toFixed(3)}</dd></div>
              <div><dt>位置 y</dt><dd>{selectedCard.y.toFixed(3)}</dd></div>
              <div><dt>朝向</dt><dd>{selectedCard.rotationDegrees}°</dd></div>
              <div><dt>操作区内</dt><dd>{selectedCard.isOnWorkspace ? '是' : '否（已拿起）'}</dd></div>
              <div><dt>输入方式</dt><dd>mouse_simulation</dd></div>
            </dl>
          ) : (
            <p>点击一张卡查看状态。</p>
          )}
          <small>C001 等编号只用于本轮交互验证；原型状态仅保存在内存中，刷新页面会重置。</small>
        </aside>
      </div>
    </section>
  )
}

function SceneWorkspace() {
  return (
    <section className="workspace-panel panel-scene">
      <header>
        <div className="panel-heading">
          <span className="panel-index">01</span>
          <h2>情境动画区</h2>
          <p>先观察初始情境；开始后在同一区域查看运动结果</p>
        </div>
        <SceneControls />
      </header>
      <div className="placeholder-content">
        <div className="track-line" />
        <div className="block-a">A</div>
        <div className="velocity-arrow">v →</div>
        <div className="scene-hint">人拉滑块动画占位</div>
      </div>
    </section>
  )
}

// Layout decision captured on 2026-11-11: the persistent digital explanation
// mirror is removed because the physical cards are the shared explanation.
// The scene sits above the card workspace to express the observe → construct
// sequence while preserving full horizontal width for both areas.
function App() {
  const [health, setHealth] = useState<HealthState | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((response) => response.json())
      .then((data: HealthState) => setHealth(data))
      .catch(() => setHealth(null))
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>触控屏实体卡原型</h1>
        <StatusBadge health={health} />
      </header>
      <main className="layout-stacked">
        <SceneWorkspace />
        <CardWorkspace />
      </main>
    </div>
  )
}

export default App
