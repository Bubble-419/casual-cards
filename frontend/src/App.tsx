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

function CardWorkspace() {
  return (
    <section className="workspace-panel panel-cards">
      <header>
        <div className="panel-heading">
          <span className="panel-index">02</span>
          <h2>卡牌操作区</h2>
          <p>观察情境后，在这里摆放、绑定与编辑实体卡牌</p>
        </div>
        <CardControls />
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
