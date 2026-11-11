import { useEffect, useState } from 'react'
import './App.css'

type HealthState = {
  status: string
  opencvVersion: string
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

function CardWorkspace() {
  return (
    <section className="workspace-panel panel-cards">
      <header>
        <span className="panel-index">01</span>
        <div>
          <h2>卡牌操作区</h2>
          <p>摆放、绑定与编辑实体卡牌</p>
        </div>
      </header>
      <div className="placeholder-content">
        <div className="paper-card card-object">物件卡</div>
        <div className="paper-card card-property">属性卡</div>
        <div className="drop-hint">后续在这里模拟或识别实体卡</div>
      </div>
    </section>
  )
}

function SceneWorkspace() {
  return (
    <section className="workspace-panel panel-scene">
      <header>
        <span className="panel-index">02</span>
        <div>
          <h2>情境动画区</h2>
          <p>情境输入决定实际动画</p>
        </div>
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

// Layout decision captured on 2026-11-11: variant C wins; the persistent
// digital explanation mirror is removed because the physical cards are the
// shared explanation. Version snapshots and feedback will open on demand.
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
        <div>
          <p className="eyebrow">CASUAL CARDS · D02 双区布局</p>
          <h1>触控屏实体卡原型</h1>
        </div>
        <StatusBadge health={health} />
      </header>
      <GlobalControls />
      <main className="layout-c">
        <CardWorkspace />
        <SceneWorkspace />
      </main>
    </div>
  )
}

export default App
