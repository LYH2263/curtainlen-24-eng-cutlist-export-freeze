# 19-curtainlen（窗帘用布）

Curtainlen — 成品宽×褶倍率 + 上下边折；换算布长米数

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4800 |
| API | http://localhost:9800 |

## 主链

窗宽层高+褶量 → 布长 → 窗户示意

## 裁幅清单导出冻结

- 导出：`POST /api/exports/cut-sheet`（或历史页「导出裁幅清单（冻结）」按钮）把当前历史首条 run 冻结为仓库内 `exports/cut_sheet_freeze.json`，含 `panels`、`meters`、按幅展开的 `lines`（无 `cut_sheet` 时按 panels 份数复制 `cut_height` 生成）与 `content_checksum`（对 `lines`+`totals` 的稳定 sha256）。
- 冻结语义：导出后再保存新 run，只要不重新导出，JSON 字节与 checksum 不变。
- 核对（只读，可重复执行，退出码 0 表示冻结完好）：

```bash
python backend/scripts/verify_cut_sheet.py
```

- 关键文件：导出 API `backend/app/routers/exports.py`；写盘 `backend/app/services/export_store.py`；checksum `backend/app/services/checksum.py`；行展开与校验 `backend/app/services/cut_sheet.py`；核对命令 `backend/scripts/verify_cut_sheet.py`。
- 测试：`cd backend && python -m pytest app/tests`（含冻结不变性与核对命令连跑两遍退出码均为 0 的用例）。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
