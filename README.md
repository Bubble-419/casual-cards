# Casual Cards

触控屏与镂空实体卡结合的力与运动解释原型。当前开发分支为 `april`。

## 当前技术结构

- `frontend/`：React、TypeScript、Vite；负责投屏界面、触控交互和 SVG 动画。
- `backend/`：Python 3.12、FastAPI、OpenCV；负责摄像头、识别、校准、保存和导出。
- `scripts/dev.sh`：同时启动前端和本地服务。
- `触控屏实体卡原型-待讨论问题.md`：设计决定与边界。
- `待开发事项.md`：逐项开发与审阅清单。

## 启动

首次克隆后安装依赖：

```bash
cd frontend && pnpm install
cd ../backend && uv sync
```

回到项目根目录，一条命令启动：

```bash
./scripts/dev.sh
```

浏览器打开 <http://localhost:5173>。开发环境可通过 `?variant=A`、`B`、`C` 切换三种布局草案，也可使用左右方向键切换。

## 单独验证

```bash
cd frontend && pnpm build
cd ../backend && uv run python -c "import cv2; assert hasattr(cv2, 'aruco')"
```

当前页面和布局草案属于第一版技术／UI 原型。卡牌语义、情境输入和自动检查必须继续遵循讨论文档，不能从占位内容推导最终规则。
