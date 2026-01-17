# FX Insight Bot - Frontend

表示専用ダッシュボード（React + TypeScript + Vite）

## 技術スタック

- React 19
- TypeScript 5.9
- Vite 7
- Tailwind CSS 4

## セットアップ

```bash
# 依存関係のインストール
npm install

# 開発サーバー起動（バックエンドが localhost:8000 で起動している必要あり）
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview
```

## 開発環境の立ち上げ

1. バックエンドを起動

```bash
cd ../backend
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

2. フロントエンドを起動

```bash
cd ../frontend
npm run dev
```

3. ブラウザで http://localhost:3000 にアクセス

## ディレクトリ構成

```
frontend/
├── src/
│   ├── api/          # API呼び出し関数
│   ├── components/   # UIコンポーネント
│   ├── hooks/        # カスタムフック
│   ├── lib/          # ユーティリティ・クライアント
│   ├── types/        # 型定義
│   ├── App.tsx       # メインコンポーネント
│   ├── main.tsx      # エントリポイント
│   └── index.css     # グローバルスタイル
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## API プロキシ

開発時は Vite の proxy 機能で `/api/*` と `/health` をバックエンド（localhost:8000）に転送します。

## 今後の予定

- Phase 5.2: Firebase Authentication（Googleログイン）
- Phase 5.3: shadcn/ui コンポーネント導入、React Query
- Phase 5.4: 追加画面（ニュース、シグナル履歴）
- Phase 5.5: ダークモード、Firebase Hosting デプロイ
