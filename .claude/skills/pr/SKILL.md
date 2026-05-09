---
description: PRを作成する
---

以下の手順でPRを作成してください。

1. 次のコマンドを並列で実行する：
   - `git status` で未追跡ファイルを確認（`-uall` フラグは使わない）
   - `git diff` でステージ済み・未ステージの差分を確認
   - `git log --oneline main..HEAD` でこのブランチのコミット一覧を確認
   - `git diff main...HEAD` でmainからの全差分を確認
   - リモートブランチの追跡状況を確認：`git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "no upstream"`

2. すべてのコミット（最新だけでなく全件）を分析してPRタイトルと本文を作成する：
   - タイトルは70文字以内で簡潔に
   - 本文は以下のフォーマットで作成する：

```
## Summary
- <変更点を箇条書き、1〜3点>

## Test plan
- [ ] <テスト項目を箇条書き>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

3. 必要に応じてリモートへプッシュする（`git push -u origin HEAD`）。

4. 以下のフォーマットでPRを作成する（HEREDOC を使う）：

```
gh pr create --title "<タイトル>" --body "$(cat <<'EOF'
## Summary
<箇条書き>

## Test plan
<チェックリスト>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

5. 作成されたPRのURLを表示する。
