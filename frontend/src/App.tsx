import { useEffect, useMemo, useState } from 'react'
import './App.css'

type VariantKey = 'A' | 'B' | 'C'

type HealthState = {
  status: string
  service: string
  opencvVersion: string
  arucoAvailable: boolean
}

const variants: Array<{ key: VariantKey; name: string }> = [
  { key: 'A', name: '协作工作台' },
  { key: 'B', name: '先观察后构建' },
  { key: 'C', name: '构建区优先' },
]

function readVariant(): VariantKey {
  const value = new URLSearchParams(window.location.search).get('variant')
  return value === 'B' || value === 'C' ? value : 'A'
}

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

function Panel({
  kind,
  title,
  note,
}: {
  kind: 'cards' | 'scene' | 'explanation'
  title: string
  note: string
}) {
  return (
    <section className={`workspace-panel panel-${kind}`}>
      <header>
        <span className="panel-index">
          {kind === 'cards' ? '01' : kind === 'scene' ? '02' : '03'}
        </span>
        <div>
          <h2>{title}</h2>
          <p>{note}</p>
        </div>
      </header>
      <div className="placeholder-content">
        {kind === 'cards' && (
          <>
            <div className="paper-card card-object">物件卡</div>
            <div className="paper-card card-property">属性卡</div>
            <div className="drop-hint">后续在这里模拟或识别实体卡</div>
          </>
        )}
        {kind === 'scene' && (
          <>
            <div className="track-line" />
            <div className="block-a">A</div>
            <div className="velocity-arrow">v →</div>
            <div className="scene-hint">人拉滑块动画占位</div>
          </>
        )}
        {kind === 'explanation' && (
          <div className="explanation-placeholder">
            <div className="node">Patient</div>
            <div className="connector" />
            <div className="node">Resultant</div>
          </div>
        )}
      </div>
    </section>
  )
}

function GlobalControls() {
  return (
    <nav className="global-controls" aria-label="任务控制">
      <button type="button">构建完成</button>
      <button type="button" className="primary">开始</button>
      <button type="button">暂停／继续</button>
      <button type="button">重新开始</button>
      <button type="button">提交最终解释</button>
    </nav>
  )
}

function VariantA() {
  return (
    <main className="layout layout-a">
      <Panel kind="cards" title="卡牌操作区" note="摆放、绑定与编辑" />
      <Panel kind="scene" title="情境动画区" note="输入决定实际动画" />
      <Panel kind="explanation" title="完整解释区" note="呈现系统读取的结构" />
    </main>
  )
}

function VariantB() {
  return (
    <main className="layout layout-b">
      <Panel kind="scene" title="情境动画区" note="先看清当前物理情境" />
      <div className="lower-workspace">
        <Panel kind="cards" title="卡牌操作区" note="构建预测解释" />
        <Panel kind="explanation" title="完整解释区" note="核对系统读取结果" />
      </div>
    </main>
  )
}

function VariantC() {
  return (
    <main className="layout layout-c">
      <Panel kind="cards" title="卡牌操作区" note="最大化实体构建空间" />
      <aside className="side-stack">
        <Panel kind="scene" title="情境动画区" note="紧凑观察窗口" />
        <Panel kind="explanation" title="完整解释区" note="随构建同步更新" />
      </aside>
    </main>
  )
}

function PrototypeSwitcher({
  current,
  onChange,
}: {
  current: VariantKey
  onChange: (key: VariantKey) => void
}) {
  const currentIndex = variants.findIndex((variant) => variant.key === current)

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      if (target?.matches('input, textarea, [contenteditable="true"]')) return
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
      const offset = event.key === 'ArrowLeft' ? -1 : 1
      onChange(variants[(currentIndex + offset + variants.length) % variants.length].key)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [currentIndex, onChange])

  const cycle = (offset: number) => {
    onChange(variants[(currentIndex + offset + variants.length) % variants.length].key)
  }

  return (
    <div className="prototype-switcher" aria-label="布局原型切换">
      <button type="button" onClick={() => cycle(-1)} aria-label="上一个布局">
        ←
      </button>
      <strong>
        {current} — {variants[currentIndex].name}
      </strong>
      <button type="button" onClick={() => cycle(1)} aria-label="下一个布局">
        →
      </button>
    </div>
  )
}

// Three throwaway variants of the shared MAXHUB workspace, switchable via ?variant=.
function App() {
  const [variant, setVariant] = useState<VariantKey>(readVariant)
  const [health, setHealth] = useState<HealthState | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((response) => response.json())
      .then((data: HealthState) => setHealth(data))
      .catch(() => setHealth(null))
  }, [])

  const currentLayout = useMemo(() => {
    if (variant === 'B') return <VariantB />
    if (variant === 'C') return <VariantC />
    return <VariantA />
  }, [variant])

  const changeVariant = (next: VariantKey) => {
    const url = new URL(window.location.href)
    url.searchParams.set('variant', next)
    window.history.replaceState({}, '', url)
    setVariant(next)
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">CASUAL CARDS · D01 技术骨架</p>
          <h1>触控屏实体卡原型</h1>
        </div>
        <StatusBadge health={health} />
      </header>
      <GlobalControls />
      {currentLayout}
      {import.meta.env.DEV && (
        <PrototypeSwitcher current={variant} onChange={changeVariant} />
      )}
    </div>
  )
}

export default App
