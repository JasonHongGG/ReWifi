# ReWifi

自動偵測 Wi‑Fi 是否「真的有網路」，若斷線或假連線就自動重連最後一次成功的 Wi‑Fi（Windows 專用）。

## 你描述的兩種狀況
- **真的斷線**：Wi‑Fi 顯示未連線/已中斷，需要重連。
- **假連線**：Wi‑Fi 顯示已連線，但實際上無法上網（DNS/路由卡住等），仍需要重連。

本工具做法：
- 用 `netsh wlan show interfaces` 判斷 Wi‑Fi 介面是否已連上 + 目前 SSID。
- 再用探針驗證「是否真的能出網」：
   - 預設用 `ping` 對外部探針（`1.1.1.1`、`8.8.8.8`）
   - 或改用 HTTP(S) 連線到指定 URL（例如 `msftconnecttest` / `generate_204`）
- 若斷線或探針失敗，會 `netsh wlan connect name=<SSID>` 重連。
- 會把「最後一次確認可上網的 SSID」寫進 `rewifi_state.json`，避免重開後不知道要連哪個。

## 直接執行
在本資料夾開 PowerShell 或 CMD：

```bash
python rewifi.py
```

或用 module 方式執行（等價）：

```bash
python -m rewifi
```

常用參數：

```bash
python rewifi.py --interval 10 --disconnect-first
```

用 HTTP(S) 探針（更貼近「真的能上網」，也比較不怕 `ping` 被擋）：

```bash
python rewifi.py --probe-mode http --interval 10
```

參數說明：
- `--interval`：每次檢查間隔秒數（預設 10）
- `--probe-mode`：探針方式（`ping` 預設、或 `http`）
- `--probes`：用逗號分隔的探針（預設 `1.1.1.1,8.8.8.8`）
- `--urls`：`--probe-mode http` 時用的 URL 清單（預設包含 `msftconnecttest` 與 `generate_204`）
- `--http-timeout-s`：`--probe-mode http` 時每個 URL 的逾時秒數（預設 3 秒）
- `--required-successes`：探針成功幾個才算有網路（預設 1）
- `--reconnect-cooldown`：兩次重連間隔至少幾秒（預設 20）
- `--disconnect-first`：重連前先斷線一次（對某些「卡住」狀況更有效）

## 開機自啟（Windows Task Scheduler）
1. 打開「工作排程器」(Task Scheduler)
2. 建立工作（Create Task）
3. **Triggers**：At startup（或 At log on）
4. **Actions**：Start a program
   - Program/script：`python`
   - Add arguments：`C:\Users\JasonHong\Desktop\CODE\_Project\ReWifi\rewifi.py --interval 10 --disconnect-first`
   - Start in：`C:\Users\JasonHong\Desktop\CODE\_Project\ReWifi`
5. **Conditions**：可勾選「Start the task only if the computer is on AC power」依你需求

