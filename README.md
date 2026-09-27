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

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。

## 裁幅清单导出（冻结）

- `POST /api/exports/cut-sheet`：把历史首条 run 按幅展开成行项目（无 cut_sheet 时按 panels 复制 cut_height），连同 panels/meters 与 `content_checksum`（对行项目+合计的 sha256）冻结写入 `exports/cut_sheet_run_<id>.json`，并在主库 `cut_sheet_orders` 追加一单。之后再写主库不影响已冻结文件。
- 历史页有「导出裁幅清单」入口。

核对（backend 目录下，纯标准库，可重复执行，退出码 0 为通过）：

```bash
python3 -m app.verify_cut_sheet
```

校验逻辑实现于 `backend/app/verify_cut_sheet.py`（重算 checksum、字节稳定性、行项目自洽、主库交叉核对），测试见 `backend/app/tests/test_export.py`。
