# 2026-05-31 バグ修正: ニュースsignal常時IGNORE / AIロット常時1000固定

## 背景

本番稼働から取引が5回程度発生したが、すべてロットが1000通貨固定だった。
AIがロットを決定しているはずなのに、意味をなしていない状態だった。
調査の結果、独立した2つのバグが見つかった。

---

## バグ1: ニュースの signal フィールドが常に "IGNORE"

### 原因

`backend/src/services/news_storage.py` の `_convert_to_news_event()` メソッドで、
`signal` 引数のデフォルト値が `"IGNORE"` になっており、呼び出し側がその引数を渡していなかった。

```python
# 修正前: signal を渡さないため常に IGNORE で保存されていた
def _convert_to_news_event(self, result, news_id, signal: str = "IGNORE"):
    ...

news_event = self._convert_to_news_event(result, news_id)  # ← signal 未指定
```

### 影響範囲

- Firestore の `news` コレクション 931件中 698件が `signal = "IGNORE"` で誤保存
- ダッシュボードのニュース一覧がすべて「無視」と表示されていた
- ロット決定には直接影響しない（ロットは `signal` ではなく `avg_sentiment` の数値で決定）

### 修正内容

`_derive_signal()` メソッドを追加し、`sentiment` の値から自動導出するよう変更。

```python
def _derive_signal(self, sentiment: int) -> str:
    if sentiment >= 1:
        return "BUY_CANDIDATE"
    elif sentiment <= -1:
        return "SELL_CANDIDATE"
    else:
        return "IGNORE"
```

### 既存データの修正

`backend/scripts/fix_news_signals.py` を作成・実行してバックフィル。

```bash
python scripts/fix_news_signals.py          # ドライラン（確認）
python scripts/fix_news_signals.py --apply  # 実際に更新
```

結果: 698件を正しい signal に更新（BUY_CANDIDATE / SELL_CANDIDATE / IGNORE）。
スクリプトは実行後に削除。

---

## バグ2: AIロットが常に 1000 固定

### 原因

`backend/src/services/rule_engine.py` の `determine_lot()` が3段階の閾値で判定していたが、
実際の `avg_sentiment` が 0〜0.5 の狭い範囲に集中しており、1000 の条件ばかり満たしていた。

**v2.0 の判定ロジック（問題あり）:**

```python
if signal == "buy":
    if sentiment > 0.5 and impact >= 3:  # ← ほぼ発動しない
        return 1500
    elif sentiment > 0:                   # ← avg_sentiment が少しでもプラスならここ
        return 1000
    elif count == 0 or sentiment == 0:    # ← 正確に0か件数0のみ
        return 500
    else:
        return 0
```

**なぜ実データで 1000 ばかりになるか:**

- Gemini が付ける `sentiment` は -2〜2 の整数
- 複数ニュースを平均すると `avg_sentiment` は 0〜0.5 程度に収まることが多い
- `0.5 > 0.5` は False なので 1500 にならない
- `sentiment > 0` は True になるので常に 1000

ダッシュボードの実ログでも `sentiment=-0.11` などの小さな値が確認できた。

### 修正内容（v2.1）

3段階の閾値を廃止し、`avg_sentiment` の絶対値を 0〜0.5 のスケールで 500〜1500 に線形マッピング。

```python
# BUY シグナルの場合
if sentiment < 0:
    return 0, "ファンダが買いに反対 → 見送り"
ratio = min(1.0, sentiment / 0.5)
lot = round((500 + ratio * 1000) / 100) * 100

# SELL シグナルの場合（abs を使用）
if sentiment > 0:
    return 0, "ファンダが売りに反対 → 見送り"
ratio = min(1.0, abs(sentiment) / 0.5)
lot = round((500 + ratio * 1000) / 100) * 100
```

**期待される分布:**

| avg_sentiment の絶対値 | ロット |
|---|---|
| 0.0（中立 / ニュースなし） | 500 |
| 0.1 | 700 |
| 0.25 | 1,000 |
| 0.4 | 1,300 |
| 0.5 以上 | 1,500 |

---

## 更新ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `backend/src/services/news_storage.py` | `_derive_signal()` 追加、`_convert_to_news_event()` の signal 自動導出 |
| `backend/src/services/rule_engine.py` | `determine_lot()` を v2.1 線形スケールに変更 |
| `frontend/src/pages/PresentationPage.tsx` | ロット決定カードを線形スケール表示に更新、Challenges に今回のバグを追加 |
| `docs/design/RULE_ENGINE_LOGIC.md` | AIロット決定ロジックを v2.1 に更新、バージョン履歴に追記 |
| `docs/TODO.md` | Phase 7 に修正2件を完了済みとして追記 |

---

## 教訓

1. **デフォルト引数は本番バグになりやすい** — `signal="IGNORE"` のように見た目が正しそうなデフォルト値ほど気づきにくい
2. **AIの決定が実際に分布しているか本番ログで確認する** — 理論上は動いていても、実データで見ると常に同じ値になっていることがある
3. **スケールと実データ範囲を合わせる** — Gemini の `sentiment` は整数 -2〜2 だが、複数ニュースの平均は 0〜0.5 に収まりやすい。閾値設計はこの実態を踏まえる必要がある
