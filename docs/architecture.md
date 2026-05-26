# アーキテクチャ

## 全体

1. **データ整備層（Python）**
   - CSV読込
   - 正規化
   - マッチング
   - JSON出力
2. **配信層（Static Hosting）**
   - `data/zip_geo.json` を静的配信
3. **表示層（Web）**
   - Leaflet地図
   - 抽選演出UI

## データフロー

`utf_ken_all.csv` + `latest.csv`
→ `scripts/build_zip_geo.py`
→ `data/zip_geo.json`
→ `web/app.js`

## マッチング戦略

- まず `pref/city` 完全一致で候補群抽出
- 町域を正規化した上でスコアリング
- 最高スコア1件を代表点として採用

## UIステート

- `idle`
- `rolling(step=1..7)`
- `resolved`

各stepで末尾一致条件を増やして候補を絞る。
