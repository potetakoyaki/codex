# FX Signal Generator (Rule-Based, Free)

Macローカルで動く、無料のFXシグナル生成＆検証システムです。

## 機能

- yfinance で 11通貨ペアの15分足を取得
- 15分足を H1/H4 にリサンプル
- ルールベース判定（BUY / SELL / WAIT）
- SQLite にシグナル/トレードを保存
- レポートで勝率・平均RR・最大DD・累積Rを表示
- API/LLM不使用

## 対象通貨ペア（固定）

- EURUSD=X
- GBPUSD=X
- USDJPY=X
- USDCHF=X
- USDCAD=X
- AUDUSD=X
- NZDUSD=X
- EURJPY=X
- GBPJPY=X
- EURGBP=X
- AUDJPY=X

## セットアップ（Mac）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 実行方法

### 1回だけ実行

```bash
python -m runner --once
```

### 15分ごとに実行

```bash
python -m runner --schedule
```

## レポート

```bash
python -m report
```

以下を表示します。

- 総トレード数（filled=1）
- 勝率
- 平均RR
- 最大DD（累積Rベース）
- 累積R

## DB

`signals.db` に以下テーブルを作成します。

- `signals`
- `trades`

## 実装ポリシー

- データ不足やNaNはWAIT
- RANGE環境はWAIT
- RR < 2.0 はWAIT
- 例外時もプロセス継続（runnerでログ出力）
- 設定値は `config.py` で変更可能
