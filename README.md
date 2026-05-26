# Nippon Roulette (Postal Roulette)

実在する日本の郵便番号からランダム抽選し、地図で「どこに飛ばされたか」を演出付きで表示するWebアプリです。

## 目的

- 存在しない郵便番号を避ける（実在データのみ抽選）
- 下位桁から確定する演出でワクワク感を維持
- Leaflet + OpenStreetMap で地図可視化
- API依存を減らし、ローカルCSVから静的データ生成

## 構成

- `docs/spec.md`: 仕様書
- `docs/architecture.md`: 設計
- `scripts/build_zip_geo.py`: 郵便番号→緯度経度JSON生成
- `web/`: フロントエンド（Vanilla JS + Leaflet）

## クイックスタート

### 1) データ生成（任意）

```bash
python3 scripts/build_zip_geo.py \
  --ken-all path/to/utf_ken_all.csv \
  --latest path/to/latest.csv \
  --out data/zip_geo.json
```

`data/zip_geo.json` がない場合でも、デモ用データで画面確認できます。

### 2) ローカル起動

```bash
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000/web/` を開いてください。

## ライセンス

データ利用時は日本郵便・地理データ提供元の利用規約に従ってください。
