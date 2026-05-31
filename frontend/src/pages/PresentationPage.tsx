import { createContext, useContext, useEffect, useState } from 'react'
import {
  Brain, TrendingUp, Newspaper, Zap, Shield, LayoutDashboard,
  DollarSign, AlertTriangle, Cpu,
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ─── Language context ──────────────────────────────────────────────────────────

type Lang = 'en' | 'ja'
const LangContext = createContext<Lang>('en')
const useLang = () => useContext(LangContext)

// ─── UI label translations ─────────────────────────────────────────────────────

const L = {
  en: {
    tagline:         'Personal Project',
    heroSub:         'An AI-Powered Automated FX Trading System',
    heroDesc:        'Technical Analysis × AI News Sentiment for automated FX trading',
    statMonth:       '/ month',
    statMonthJa:     '月間運用コスト',
    statNews:        'daily news',
    statNewsJa:      '毎日のニュース収集',
    statLive:        'since Feb 2026',
    statLiveJa:      '2026年2月より本番稼働',
    scroll:          'scroll',
    problem:         'Problem',
    solution:        'Solution',
    lesson:          'Lesson Learned',
    phase:           'Phase',
    maxScore:        'Max: 8 pts per direction (Trend 3 + RSI 2 + News 3)',
    monthlyCost:     'Monthly operating cost',
    budgetTarget:    'vs. ¥1,000 budget target',
    budgetUsage:     'Budget usage',
    coffeeText:      '"Less than 2 cups of coffee per month"',
    costTitle:       'Cost Breakdown by Service',
    total:           'Total',
    scoringRules:    'Scoring Rules',
    scoringSub:      'buy / sell — 0 to 8 pts each',
    decisionLogic:   'Decision Logic',
    lotSizing:       'AI Lot Sizing',
    lotSizingSub:    'Dynamic lot control based on confidence',
    lowConf:         'Low confidence',
    medConf:         'Medium confidence',
    highConf:        'High confidence',
    gcpLabel:        'Google Cloud Platform',
    externalLabel:   'External Services',
    calledBy:        '← Called by Cloud Run (Private)',
    readsFrom:       '→ Reads from Cloud Run (Public)',
    nextTitle:       "What's Next",
    nextSub:         '今後の展開',
    nextDesc:        'The current system uses rule-based signals (if/else). The next project separates direction from confidence using meta-labeling with machine learning.',
    nextDescSub:     '現システムはルールベース。次プロジェクトではメタラベリング戦略で「方向」と「確信度」を分離。',
    layer1:          'Layer 1 · Direction',
    layer1desc:      '→ Primary signal: Buy / Sell',
    layer2:          'Layer 2 · Confidence',
    layer2desc:      '→ Predicts success probability → controls lot size',
    lotControl:      'Lot Control',
    newFeatures:     'New Features',
    lotSkip:         'skip',
    strategyTitle:   'Strategy — Meta-Labeling',
    inProgress:      '🔄 In Progress',
    planned:         '📋 Planned',
  },
  ja: {
    tagline:         '個人プロジェクト',
    heroSub:         'AI搭載 FX自動売買システム',
    heroDesc:        'テクニカル分析 × AI ニュース解析による FX 自動売買',
    statMonth:       '/ 月',
    statMonthJa:     'Monthly operating cost',
    statNews:        '回 / 日',
    statNewsJa:      'Daily news analysis',
    statLive:        '2026年2月〜',
    statLiveJa:      'Live since Feb 2026',
    scroll:          'スクロール',
    problem:         '問題',
    solution:        '解決策',
    lesson:          '教訓',
    phase:           'フェーズ',
    maxScore:        '最大スコア: 各方向8点（トレンド3 + RSI2 + ニュース3）',
    monthlyCost:     '月間運用コスト',
    budgetTarget:    '予算 ¥1,000/月 に対して',
    budgetUsage:     '予算消化率',
    coffeeText:      '「コーヒー2杯分以下で本番稼働」',
    costTitle:       'サービス別コスト内訳',
    total:           '合計',
    scoringRules:    'スコアリングルール',
    scoringSub:      'buy / sell それぞれ 0〜8 点',
    decisionLogic:   '判定ロジック',
    lotSizing:       'AIロット決定',
    lotSizingSub:    '確信度に応じたロット動的制御',
    lowConf:         '確信度 低',
    medConf:         '確信度 中',
    highConf:        '確信度 高',
    gcpLabel:        'Google Cloud Platform',
    externalLabel:   '外部サービス',
    calledBy:        '← Cloud Run（プライベート）から呼び出し',
    readsFrom:       '→ Cloud Run（パブリック）から取得',
    nextTitle:       '今後の展開',
    nextSub:         "What's Next",
    nextDesc:        '現システムはルールベース（if/else）のシグナル判断。次プロジェクトでは機械学習によるメタラベリングで「方向判断」と「確信度判定」を分離する。',
    nextDescSub:     'The current system uses rule-based signals. The next project separates direction from confidence using meta-labeling with ML.',
    layer1:          'レイヤー1 · 方向の決定',
    layer1desc:      '→ 1次シグナル: Buy / Sell',
    layer2:          'レイヤー2 · 確信度の判定',
    layer2desc:      '→ 成功確率を予測 → ロットを動的制御',
    lotControl:      'ロット制御',
    newFeatures:     '新規特徴量',
    lotSkip:         '見送り',
    strategyTitle:   '戦略 — メタラベリング',
    inProgress:      '🔄 進行中',
    planned:         '📋 未着手',
  },
} as const

// ─── Nav sections ──────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: 'hero',         labelEn: 'Top',          labelJa: 'トップ' },
  { id: 'motivation',   labelEn: 'Why',           labelJa: '経緯' },
  { id: 'features',     labelEn: 'Features',      labelJa: '機能' },
  { id: 'architecture', labelEn: 'Architecture',  labelJa: '構成' },
  { id: 'dataflow',     labelEn: 'Flow',          labelJa: '流れ' },
  { id: 'techstack',    labelEn: 'Stack',         labelJa: 'スタック' },
  { id: 'signals',      labelEn: 'Signals',       labelJa: 'シグナル' },
  { id: 'cost',         labelEn: 'Cost',          labelJa: 'コスト' },
  { id: 'challenges',   labelEn: 'Challenges',    labelJa: '苦労' },
  { id: 'timeline',     labelEn: 'Timeline',      labelJa: '経歴' },
  { id: 'nextsteps',    labelEn: 'Next',          labelJa: '次へ' },
]

// ─── Shared UI helpers ──────────────────────────────────────────────────────────

function SectionHeader({ en, ja, light = false }: { en: string; ja: string; light?: boolean }) {
  const lang = useLang()
  const primary   = lang === 'en' ? en : ja
  const secondary = lang === 'en' ? ja : en
  return (
    <div className="text-center mb-16">
      <h2 className={cn('text-4xl font-bold', light ? 'text-white' : 'text-gray-900 dark:text-white')}>{primary}</h2>
      <p className={cn('mt-2 text-xs tracking-widest uppercase', light ? 'text-slate-500' : 'text-gray-400')}>{secondary}</p>
    </div>
  )
}

/** Architecture diagram box */
function ABox({ label, sub, accent }: { label: string; sub?: string; accent: string }) {
  return (
    <div className={cn('rounded-xl px-4 py-3 text-center border-2', accent)}>
      <div className="font-semibold text-sm">{label}</div>
      {sub && <div className="text-xs opacity-60 mt-0.5">{sub}</div>}
    </div>
  )
}

/** Downward arrow between architecture boxes */
function VArrow({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center py-0.5">
      {label && <span className="text-xs text-gray-400 mb-1">{label}</span>}
      <div className="w-px h-5 bg-gray-300" />
      <svg width="10" height="6" viewBox="0 0 10 6" className="fill-gray-300">
        <path d="M5 6L0 0h10L5 6z" />
      </svg>
    </div>
  )
}

// ─── Section 1: Hero ───────────────────────────────────────────────────────────

function HeroSection() {
  const lang = useLang()
  const l = L[lang]
  return (
    <section id="hero" className="min-h-screen bg-slate-900 flex flex-col items-center justify-center px-6 text-white relative">
      <div className="text-center max-w-4xl w-full">
        <span className="inline-block text-slate-500 text-xs tracking-[0.3em] uppercase mb-6">
          {l.tagline} · {lang === 'en' ? '個人プロジェクト' : 'Personal Project'}
        </span>
        <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tight mb-6">
          FX Insight Bot
        </h1>
        <p className="text-xl md:text-2xl text-slate-300 mb-1">{l.heroSub}</p>
        <p className="text-sm text-slate-600 mb-16">{l.heroDesc}</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-5">
            <div className="text-3xl font-bold text-blue-400">~¥265</div>
            <div className="text-slate-400 text-sm mt-0.5">{l.statMonth}</div>
            <div className="text-slate-600 text-xs mt-1">{l.statMonthJa}</div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-5">
            <div className="text-3xl font-bold text-green-400">2×</div>
            <div className="text-slate-400 text-sm mt-0.5">{l.statNews}</div>
            <div className="text-slate-600 text-xs mt-1">{l.statNewsJa}</div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-5">
            <div className="text-3xl font-bold text-purple-400">Live</div>
            <div className="text-slate-400 text-sm mt-0.5">{l.statLive}</div>
            <div className="text-slate-600 text-xs mt-1">{l.statLiveJa}</div>
          </div>
        </div>
      </div>

      <div className="absolute bottom-8 flex flex-col items-center gap-1 text-slate-600 text-xs">
        <span>{l.scroll}</span>
        <svg className="w-4 h-4 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </section>
  )
}

// ─── Section 2: Motivation ─────────────────────────────────────────────────────

const MOTIVATIONS = [
  {
    Icon: Brain,
    en: 'Can AI Beat Manual Trading?',
    ja: 'AIは手動売買に勝てるか？',
    bodyEn: 'Manual FX trading is emotionally exhausting — always watching screens, second-guessing decisions. Could an AI make more consistent calls?',
    bodyJa: '手動売買は感情的に疲弊する。常に画面を監視し、判断を迷い続ける。AIならより一貫した判断ができるのでは？という疑問からスタート。',
    subEn: '個人的な興味・きっかけ',
    subJa: 'Personal motivation',
    accent: 'border-blue-500',
    iconCls: 'bg-blue-100 text-blue-600',
  },
  {
    Icon: Cpu,
    en: 'GCP + Vertex AI in Production',
    ja: 'GCP + Vertex AI を本番で動かす',
    bodyEn: 'I wanted to use Google Cloud Platform and Vertex AI not in a tutorial, but in a real, running system with actual data and live API calls.',
    bodyJa: 'チュートリアルではなく、実際の本番環境でGCPとVertex AIを使いたかった。実データとライブAPIで動かすことで深く理解できると考えた。',
    subEn: '技術的な学習目的',
    subJa: 'Technical learning',
    accent: 'border-purple-500',
    iconCls: 'bg-purple-100 text-purple-600',
  },
  {
    Icon: DollarSign,
    en: 'Under ¥1,000 / Month Challenge',
    ja: '月¥1,000以下という制約',
    bodyEn: 'A self-imposed constraint: build and run an AI-powered trading system for the price of a coffee. Forces creative use of free tiers.',
    bodyJa: '自ら課した縛り: コーヒー1杯分の予算でAI自動売買システムを本番運用する。無料枠を創造的に活用することを強制する設計チャレンジ。',
    subEn: 'コスト制約への挑戦',
    subJa: 'Cost-optimization challenge',
    accent: 'border-green-500',
    iconCls: 'bg-green-100 text-green-600',
  },
]

function MotivationSection() {
  const lang = useLang()
  return (
    <section id="motivation" className="py-24 bg-white dark:bg-gray-950 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="Why I Built This" ja="作った経緯" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {MOTIVATIONS.map(({ Icon, en, ja, bodyEn, bodyJa, subEn, subJa, accent, iconCls }) => (
            <div key={en} className={cn('rounded-2xl bg-white dark:bg-gray-900 p-8 shadow-sm border-l-4', accent)}>
              <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-5', iconCls)}>
                <Icon className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white leading-snug mb-1">
                {lang === 'en' ? en : ja}
              </h3>
              <p className="text-xs text-gray-400 mb-4">{lang === 'en' ? subEn : subJa}</p>
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {lang === 'en' ? bodyEn : bodyJa}
              </p>
              <p className="text-xs text-gray-400 mt-3 leading-relaxed">
                {lang === 'en' ? bodyJa : bodyEn}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Section 3: Features ───────────────────────────────────────────────────────

const FEATURES = [
  {
    Icon: Newspaper,
    en: 'News Intelligence', ja: 'ニュース収集',
    bodyEn: 'Real-time FX news via Gemini Grounding + Google Search. Grounded in live results — no hallucination.',
    bodyJa: 'Gemini GroundingとGoogle検索でリアルタイムのFXニュースを収集。ライブ検索結果に基づくため幻覚なし。',
    bg: 'bg-blue-50', ic: 'text-blue-600',
  },
  {
    Icon: Brain,
    en: 'AI Sentiment Analysis', ja: 'AI感情分析',
    bodyEn: 'Gemini 2.5 Flash scores each article: −2 (very bearish) to +2 (very bullish), with impact level and time horizon.',
    bodyJa: 'Gemini 2.5 Flashが各記事をスコアリング: −2（超弱気）〜+2（超強気）。影響度・時間軸も判定。',
    bg: 'bg-purple-50', ic: 'text-purple-600',
  },
  {
    Icon: TrendingUp,
    en: 'Technical Analysis', ja: 'テクニカル分析',
    bodyEn: 'MA20/50, RSI(14), MACD(12,26,9) computed on 1-hour candles. Identifies trend direction and momentum.',
    bodyJa: 'MA20/50、RSI(14)、MACD(12,26,9)を1時間足で計算。トレンドの方向とモメンタムを識別。',
    bg: 'bg-emerald-50', ic: 'text-emerald-600',
  },
  {
    Icon: Zap,
    en: 'Signal Engine', ja: 'シグナルエンジン',
    bodyEn: 'Rule-based engine integrates technical + news scores. Generates BUY / SELL / HOLD with a 0–8 point scoring system.',
    bodyJa: 'テクニカル+ニューススコアを統合するルールベースエンジン。0〜8点のスコアリングでBUY/SELL/HOLDを生成。',
    bg: 'bg-yellow-50', ic: 'text-yellow-600',
  },
  {
    Icon: Shield,
    en: 'Automated Trading', ja: '自動売買',
    bodyEn: 'IFDOCO orders set entry + stop-loss + take-profit atomically in one API call. Eliminates orphaned positions.',
    bodyJa: 'IFDOCO注文でエントリー+SL+TPを1回のAPIコールで原子的に設定。孤立ポジションを排除。',
    bg: 'bg-red-50', ic: 'text-red-600',
  },
  {
    Icon: LayoutDashboard,
    en: 'Web Dashboard', ja: 'Webダッシュボード',
    bodyEn: 'React + TypeScript dashboard showing live positions, P&L, signals, and news. Auto-refreshes every 30 seconds.',
    bodyJa: 'React+TypeScriptのダッシュボードでライブポジション・損益・シグナル・ニュースを表示。30秒ごとに自動更新。',
    bg: 'bg-indigo-50', ic: 'text-indigo-600',
  },
]

function FeaturesSection() {
  const lang = useLang()
  return (
    <section id="features" className="py-24 bg-gray-50 dark:bg-gray-900 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="What It Does" ja="主な機能" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ Icon, en, ja, bodyEn, bodyJa, bg, ic }) => (
            <div key={en} className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm">
              <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-4', bg)}>
                <Icon className={cn('w-5 h-5', ic)} />
              </div>
              <h3 className="font-bold text-gray-900 dark:text-white mb-0.5">{lang === 'en' ? en : ja}</h3>
              <p className="text-xs text-gray-400 mb-3">{lang === 'en' ? ja : en}</p>
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {lang === 'en' ? bodyEn : bodyJa}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Section 4: Architecture ───────────────────────────────────────────────────

function ArchitectureSection() {
  const lang = useLang()
  const l = L[lang]
  return (
    <section id="architecture" className="py-24 bg-white dark:bg-gray-950 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="System Architecture" ja="システム構成" />

        <div className="flex flex-col lg:flex-row gap-16 items-start justify-center">

          <div className="flex-1">
            <p className="text-xs text-center text-gray-400 uppercase tracking-widest mb-6">{l.gcpLabel}</p>
            <div className="flex flex-col items-center">
              <ABox label="Cloud Scheduler" sub={lang === 'en' ? '3 cron jobs' : '3つのCronジョブ'} accent="border-amber-400 bg-amber-50 text-amber-900" />
              <VArrow label={lang === 'en' ? 'HTTP POST · OIDC Auth' : 'HTTP POST（OIDC認証）'} />
              <ABox label="Cloud Run (Private)" sub={lang === 'en' ? 'FastAPI — trade & news services' : 'FastAPI — 取引・ニュースサービス'} accent="border-purple-400 bg-purple-50 text-purple-900" />
              <VArrow />
              <div className="flex gap-4 flex-wrap justify-center">
                <ABox label="Firestore" sub={lang === 'en' ? 'Last 3 months' : '直近3ヶ月'} accent="border-blue-400 bg-blue-50 text-blue-900" />
                <ABox label="BigQuery" sub={lang === 'en' ? 'Full history' : '全履歴・分析'} accent="border-green-400 bg-green-50 text-green-900" />
              </div>
              <div className="mt-4 w-full border-t border-dashed border-gray-200 dark:border-gray-700 pt-4">
                <ABox label="Cloud Run (Public)" sub={lang === 'en' ? 'Read-only endpoints for dashboard' : 'ダッシュボード向け読み取り専用API'} accent="border-slate-400 bg-slate-50 text-slate-900" />
              </div>
            </div>
          </div>

          <div className="flex-1">
            <p className="text-xs text-center text-gray-400 uppercase tracking-widest mb-6">{l.externalLabel}</p>
            <div className="flex flex-col gap-5">
              <div>
                <ABox label="Vertex AI (Gemini 2.5 Flash)" sub={lang === 'en' ? 'News analysis + Google Search Grounding' : 'ニュース分析 + Google Grounding'} accent="border-indigo-400 bg-indigo-50 text-indigo-900" />
                <p className="text-center text-xs text-gray-400 mt-1.5">{l.calledBy}</p>
              </div>
              <div>
                <ABox label="GMO Coin API" sub={lang === 'en' ? 'Public REST (prices) + Private REST (orders)' : 'パブリック（価格）+ プライベート（注文）'} accent="border-orange-400 bg-orange-50 text-orange-900" />
                <p className="text-center text-xs text-gray-400 mt-1.5">{l.calledBy}</p>
              </div>
              <div>
                <ABox label="Firebase Hosting" sub={lang === 'en' ? 'React SPA Dashboard' : 'React SPA ダッシュボード'} accent="border-red-400 bg-red-50 text-red-900" />
                <p className="text-center text-xs text-gray-400 mt-1.5">{l.readsFrom}</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}

// ─── Section 5: Data Flow ──────────────────────────────────────────────────────

const NEWS_STEPS = [
  { en: 'Generate search queries',          ja: '検索クエリ生成（USD/JPY・EUR/JPY・金融政策 など）' },
  { en: 'Fetch news via Gemini Grounding',  ja: 'Gemini Groundingでリアルタイムニュースを取得（幻覚なし）' },
  { en: 'AI scores each article',           ja: '感情 −2〜+2・影響度 1〜5・時間軸を判定' },
  { en: 'Save to Firestore',               ja: '重複排除してFirestoreに保存' },
  { en: 'Export to BigQuery',              ja: '日次で全履歴に追記' },
]

const TRADE_STEPS = [
  { en: 'Fetch 100 × 1h candles from GMO', ja: '直近100本の1時間足を取得' },
  { en: 'Compute MA / RSI / MACD',          ja: 'テクニカル指標を計算' },
  { en: 'Fetch recent news (impact ≥ 3)',   ja: '直近24hの高影響ニュースを取得' },
  { en: 'Score: buy_score & sell_score (0–8)', ja: 'テクニカル+ニュースでスコアリング' },
  { en: 'Signal: BUY / SELL / HOLD',        ja: 'score ≥ 4 でシグナル発行' },
  { en: 'AI determines lot size (0–1,500)', ja: '確信度に応じてロット決定' },
  { en: 'Risk checks → IFDOCO order',       ja: 'リスクチェック通過後にIFDOCO注文発行' },
]

function FlowStep({ idx, en, ja }: { idx: number; en: string; ja: string }) {
  const lang = useLang()
  return (
    <div className="flex items-start gap-3">
      <div className="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300 shrink-0 mt-0.5">
        {idx}
      </div>
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-white">{lang === 'en' ? en : ja}</p>
        <p className="text-xs text-gray-400 mt-0.5">{lang === 'en' ? ja : en}</p>
      </div>
    </div>
  )
}

function DataFlowSection() {
  const lang = useLang()
  return (
    <section id="dataflow" className="py-24 bg-gray-50 dark:bg-gray-900 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="How It Works" ja="処理の流れ" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Newspaper className="w-5 h-5 text-blue-500 shrink-0" />
              <h3 className="font-bold text-gray-900 dark:text-white">
                {lang === 'en' ? 'News Collection Pipeline' : 'ニュース収集パイプライン'}
              </h3>
            </div>
            <p className="text-xs text-gray-400 mb-6">
              {lang === 'en' ? '毎日 8:00 / 20:00 JST' : 'Daily 8:00 / 20:00 JST'}
            </p>
            <div className="flex flex-col gap-4">
              {NEWS_STEPS.map((s, i) => <FlowStep key={i} idx={i + 1} {...s} />)}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-green-500 shrink-0" />
              <h3 className="font-bold text-gray-900 dark:text-white">
                {lang === 'en' ? 'Trading Execution Pipeline' : '取引実行パイプライン'}
              </h3>
            </div>
            <p className="text-xs text-gray-400 mb-6">
              {lang === 'en' ? '平日 9:00 / 21:00 JST' : 'Weekdays 9:00 / 21:00 JST'}
            </p>
            <div className="flex flex-col gap-4">
              {TRADE_STEPS.map((s, i) => <FlowStep key={i} idx={i + 1} {...s} />)}
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}

// ─── Section 6: Tech Stack ─────────────────────────────────────────────────────

const STACK = [
  { layerEn: 'AI / Analysis',  layerJa: 'AI分析',          tech: 'Vertex AI (Gemini 2.5 Flash)',  reasonEn: 'Thinking mode · GCP-native · grounding with Google Search',                              reasonJa: 'Thinkingモード対応・GCPネイティブ・Google検索グラウンディング' },
  { layerEn: 'News Source',    layerJa: 'ニュース取得',     tech: 'Google Search Grounding',       reasonEn: 'Real-time results · no hallucination · 1,500 searches/day free',                            reasonJa: 'リアルタイム結果・幻覚なし・1日1,500件まで無料' },
  { layerEn: 'Backend',        layerJa: 'バックエンド',     tech: 'FastAPI + Cloud Run',           reasonEn: 'Stateless · containerized · free tier (60 req/month)',                                      reasonJa: 'ステートレス・コンテナ化・無料枠（60リクエスト/月）' },
  { layerEn: 'Indicators',     layerJa: 'テクニカル指標',   tech: 'pandas (custom formulas)',      reasonEn: 'pandas-ta had Python version conflicts → built MA/RSI/MACD from scratch',                   reasonJa: 'pandas-taのバージョン非互換問題を回避するため自前実装' },
  { layerEn: 'DB — recent',    layerJa: 'DB（短期）',       tech: 'Firestore',                     reasonEn: 'Schema-less · GCP-native · auto-scaling · 3-month retention',                              reasonJa: 'スキーマレス・GCPネイティブ・オートスケール' },
  { layerEn: 'DB — history',   layerJa: 'DB（長期）',       tech: 'BigQuery',                      reasonEn: 'SQL analytics on long-term trade history · permanent storage',                              reasonJa: 'SQLで長期取引履歴を分析・永続ストレージ' },
  { layerEn: 'Frontend',       layerJa: 'フロントエンド',   tech: 'React + TypeScript + Vite',    reasonEn: 'Type-safe · fast builds · Recharts for charts',                                             reasonJa: '型安全・高速ビルド・Rechartsでグラフ描画' },
  { layerEn: 'Hosting',        layerJa: 'ホスティング',     tech: 'Firebase Hosting',              reasonEn: 'Free · SPA-ready · GCP-native CDN',                                                        reasonJa: '無料・SPA対応・GCPネイティブCDN' },
  { layerEn: 'Scheduling',     layerJa: 'スケジューリング', tech: 'Cloud Scheduler',               reasonEn: 'First 3 jobs free · reliable cron · OIDC auth to Cloud Run',                               reasonJa: '3ジョブまで無料・安定Cron・Cloud RunへOIDC認証' },
  { layerEn: 'Trading API',    layerJa: '取引API',          tech: 'GMO Coin REST API',             reasonEn: 'Free · IFDOCO order support · rate limit 6 req/sec',                                       reasonJa: '無料・IFDOCO注文対応・レート制限6リクエスト/秒' },
]

function TechStackSection() {
  const lang = useLang()
  return (
    <section id="techstack" className="py-24 bg-white dark:bg-gray-950 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeader en="Technology Stack" ja="技術スタック" />
        <div className="overflow-x-auto rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-4 font-semibold">{lang === 'en' ? 'Layer' : 'レイヤー'}</th>
                <th className="px-6 py-4 font-semibold">{lang === 'en' ? 'Technology' : '技術'}</th>
                <th className="px-6 py-4 font-semibold">{lang === 'en' ? 'Why' : '選定理由'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
              {STACK.map(({ layerEn, layerJa, tech, reasonEn, reasonJa }) => (
                <tr key={layerEn} className="hover:bg-gray-50/50 dark:hover:bg-gray-900/50 transition-colors">
                  <td className="px-6 py-4">
                    <span className="text-gray-700 dark:text-gray-200 font-medium">
                      {lang === 'en' ? layerEn : layerJa}
                    </span>
                    <span className="block text-xs text-gray-400 mt-0.5">
                      {lang === 'en' ? layerJa : layerEn}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">{tech}</td>
                  <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs leading-relaxed">
                    {lang === 'en' ? reasonEn : reasonJa}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

// ─── Section 7: Signal Engine ──────────────────────────────────────────────────

const SIGNAL_RULES = [
  { en: 'Uptrend + bullish momentum',   ja: '上昇トレンド + 強気モメンタム', buy: 3, sell: 0 },
  { en: 'Downtrend + bearish momentum', ja: '下落トレンド + 弱気モメンタム', buy: 0, sell: 3 },
  { en: 'RSI oversold (< 30)',          ja: 'RSI 売られすぎ（< 30）',        buy: 2, sell: 0 },
  { en: 'RSI overbought (> 70)',        ja: 'RSI 買われすぎ（> 70）',        buy: 0, sell: 2 },
  { en: 'Positive news (impact ≥ 3)',   ja: 'ポジティブニュース（影響度 ≥ 3）', buy: 3, sell: 0 },
  { en: 'Negative news (impact ≥ 3)',   ja: 'ネガティブニュース（影響度 ≥ 3）', buy: 0, sell: 3 },
]

function ScoreDots({ score, max, color }: { score: number; max: number; color: string }) {
  return (
    <div className="flex gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <div key={i} className={cn('w-2.5 h-2.5 rounded-full', i < score ? color : 'bg-gray-200 dark:bg-gray-700')} />
      ))}
    </div>
  )
}

function SignalSection() {
  const lang = useLang()
  const l = L[lang]
  return (
    <section id="signals" className="py-24 bg-gray-50 dark:bg-gray-900 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="Signal Generation Engine" ja="シグナル生成エンジン" />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm">
            <h3 className="font-bold text-gray-900 dark:text-white mb-1">{l.scoringRules}</h3>
            <p className="text-xs text-gray-400 mb-6">{l.scoringSub}</p>
            <div className="flex flex-col gap-4">
              {SIGNAL_RULES.map(({ en, ja, buy, sell }) => (
                <div key={en} className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{lang === 'en' ? en : ja}</p>
                    <p className="text-xs text-gray-400">{lang === 'en' ? ja : en}</p>
                  </div>
                  <div className="flex gap-4 shrink-0">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-xs font-semibold text-green-600">buy</span>
                      <ScoreDots score={buy} max={3} color="bg-green-500" />
                    </div>
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-xs font-semibold text-red-500">sell</span>
                      <ScoreDots score={sell} max={3} color="bg-red-500" />
                    </div>
                  </div>
                </div>
              ))}
              <div className="pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-400">
                {l.maxScore}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm">
              <h3 className="font-bold text-gray-900 dark:text-white mb-1">{l.decisionLogic}</h3>
              <p className="text-xs text-gray-400 mb-5">{lang === 'en' ? '判定ロジック' : 'Decision Logic'}</p>
              <div className="flex flex-col gap-3">
                {[
                  { cond: 'buy_score ≥ 4  AND  sell_score ≤ 1', signal: 'BUY',  cls: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-950 dark:border-green-800 dark:text-green-300' },
                  { cond: 'sell_score ≥ 4  AND  buy_score ≤ 1', signal: 'SELL', cls: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950 dark:border-red-800 dark:text-red-300' },
                  { cond: lang === 'en' ? 'Otherwise (conflicting / weak)' : 'それ以外（シグナル競合または弱い）', signal: 'HOLD', cls: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-300' },
                ].map(({ cond, signal, cls }) => (
                  <div key={signal} className={cn('rounded-xl border px-4 py-3', cls)}>
                    <code className="text-xs">{cond}</code>
                    <span className="ml-2 font-bold text-sm">→ {signal}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm">
              <h3 className="font-bold text-gray-900 dark:text-white mb-1">{l.lotSizing}</h3>
              <p className="text-xs text-gray-400 mb-5">{l.lotSizingSub}</p>
              <div className="flex flex-col gap-3">
                {[
                  { confKey: 'lowConf',  lot: `0 (${l.lotSkip})`, cls: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300' },
                  { confKey: 'medConf',  lot: '500 / 1,000',       cls: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300' },
                  { confKey: 'highConf', lot: '1,500',              cls: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300' },
                ].map(({ confKey, lot, cls }) => (
                  <div key={confKey} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">{l[confKey as keyof typeof l]}</span>
                    <span className={cn('px-3 py-1 rounded-full text-xs font-semibold', cls)}>{lot} units</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}

// ─── Section 8: Cost ───────────────────────────────────────────────────────────

const COST_ITEMS = [
  { nameEn: 'Vertex AI (Gemini 2.5 Flash, Thinking mode)', nameJa: 'Vertex AI（Gemini 2.5 Flash・Thinkingモード）', cost: '~¥181', free: false },
  { nameEn: 'Artifact Registry (Docker image storage)',    nameJa: 'Artifact Registry（Dockerイメージ保存）',        cost: '~¥52',  free: false },
  { nameEn: 'Cloud Storage (build cache)',                 nameJa: 'Cloud Storage（ビルドキャッシュ）',              cost: '~¥7',   free: false },
  { nameEn: 'Cloud Run (2 services)',                      nameJa: 'Cloud Run（2サービス）',                         cost: '¥0',    free: true },
  { nameEn: 'Firestore',                                   nameJa: 'Firestore',                                      cost: '¥0',    free: true },
  { nameEn: 'Cloud Scheduler (3 jobs)',                    nameJa: 'Cloud Scheduler（3ジョブ）',                     cost: '¥0',    free: true },
  { nameEn: 'Firebase Hosting',                            nameJa: 'Firebase Hosting',                               cost: '¥0',    free: true },
  { nameEn: 'GMO Coin API',                                nameJa: 'GMO コイン API',                                 cost: '¥0',    free: true },
]

function CostSection() {
  const lang = useLang()
  const l = L[lang]
  const pct = 27

  return (
    <section id="cost" className="py-24 bg-white dark:bg-gray-950 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="Cost Efficiency" ja="コスト効率" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">

          <div className="flex flex-col gap-6">
            <div className="rounded-2xl bg-slate-900 text-white p-10 text-center">
              <p className="text-slate-400 text-sm mb-2">{l.monthlyCost}</p>
              <p className="text-6xl font-black">~¥265</p>
              <p className="text-slate-500 text-sm mt-3">{l.budgetTarget}</p>
            </div>
            <div className="rounded-2xl border border-gray-100 dark:border-gray-800 p-6 shadow-sm">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600 dark:text-gray-300">{l.budgetUsage}</span>
                <span className="font-semibold text-gray-900 dark:text-white">{pct}%</span>
              </div>
              <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <span>¥0</span>
                <span>¥1,000 / {lang === 'en' ? 'month' : '月'}</span>
              </div>
              <p className="text-center text-xs text-gray-400 mt-4 italic">{l.coffeeText}</p>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200">{l.costTitle}</h3>
            </div>
            <div className="divide-y divide-gray-50 dark:divide-gray-800">
              {COST_ITEMS.map(({ nameEn, nameJa, cost, free }) => (
                <div key={nameEn} className="flex items-center justify-between px-6 py-3">
                  <p className="text-sm text-gray-700 dark:text-gray-300">{lang === 'en' ? nameEn : nameJa}</p>
                  <span className={cn('text-sm font-semibold shrink-0 ml-4', free ? 'text-green-600' : 'text-gray-900 dark:text-white')}>
                    {cost}
                  </span>
                </div>
              ))}
              <div className="flex items-center justify-between px-6 py-4 bg-gray-50 dark:bg-gray-900">
                <p className="text-sm font-bold text-gray-900 dark:text-white">{l.total}</p>
                <span className="text-sm font-bold text-gray-900 dark:text-white">~¥265 <span className="text-xs font-normal text-gray-400">(incl. tax)</span></span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}

// ─── Section 9: Challenges ─────────────────────────────────────────────────────

const CHALLENGES = [
  {
    en: 'Gemini JSON Output Instability',
    ja: 'Gemini の JSON 出力が不安定',
    problemEn: 'Using Grounding + JSON response format simultaneously caused API errors.',
    problemJa: 'Grounding と JSON 形式指定を同時に使うと API がエラーを返す。',
    solutionEn: 'Output as Markdown code blocks (```json), then parse the response manually.',
    solutionJa: 'Markdownコードブロックとして出力させ、レスポンスを自前でパース。',
    lessonEn: "LLM API constraints often aren't documented. Test each feature combination.",
    lessonJa: 'LLM APIの制約はドキュメントに書かれていないことが多い。各機能の組み合わせを必ずテストする。',
    accent: 'border-orange-400',
    iconCls: 'bg-orange-100 text-orange-600',
  },
  {
    en: 'GMO API Numeric Precision Error (ERR-5114)',
    ja: '価格フォーマットエラー（ERR-5114）',
    problemEn: "Python's float precision exceeded GMO's tickSize spec (0.001 for JPY pairs).",
    problemJa: 'Python の浮動小数点精度が GMO の tickSize（0.001）を超えてエラーが出た。',
    solutionEn: 'Standardized with round(price, 3) and f"{price:.3f}" string formatting.',
    solutionJa: 'round(price, 3) と文字列フォーマット f"{price:.3f}" で精度を統一。',
    lessonEn: 'Always verify numeric precision specs when working with financial APIs.',
    lessonJa: '金融APIを使う際は数値精度の仕様を必ず確認する。',
    accent: 'border-red-400',
    iconCls: 'bg-red-100 text-red-600',
  },
  {
    en: 'Cloud Functions → Cloud Run Migration',
    ja: 'Cloud Functions → Cloud Run への移行',
    problemEn: 'Cloud Functions could not include the backend/src directory as deployment source.',
    problemJa: 'Cloud Functions が backend/src ディレクトリをデプロイソースに含められなかった。',
    solutionEn: 'Created a Dockerfile and deployed the entire app as a container to Cloud Run.',
    solutionJa: 'Dockerfile を作成し、アプリごとコンテナとして Cloud Run にデプロイ。',
    lessonEn: 'Cloud Run offers far more deployment flexibility than Cloud Functions.',
    lessonJa: 'Cloud Run は Cloud Functions より圧倒的にデプロイの柔軟性が高い。',
    accent: 'border-purple-400',
    iconCls: 'bg-purple-100 text-purple-600',
  },
  {
    en: 'Low Trade Frequency (~1 trade / month)',
    ja: '取引頻度が低い（月1回程度）',
    problemEn: 'MACD crossover events are rare. Setting score ≥ 4 without backtesting was too conservative.',
    problemJa: 'MACDクロスオーバーは稀なイベント。バックテストなしで閾値を設定したため保守的すぎた。',
    solutionEn: 'Tuning plan: change MACD condition from crossover to histogram > 0.',
    solutionJa: 'MACD判定を「クロスオーバー瞬間」から「ヒストグラム > 0」に変更予定。',
    lessonEn: 'Always validate signal thresholds with backtesting before going live.',
    lessonJa: '本番前にシグナルの閾値をバックテストで必ず検証する。',
    accent: 'border-blue-400',
    iconCls: 'bg-blue-100 text-blue-600',
  },
]

function ChallengesSection() {
  const lang = useLang()
  const l = L[lang]
  return (
    <section id="challenges" className="py-24 bg-gray-50 dark:bg-gray-900 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en="Challenges & Solutions" ja="苦労したこと・解決策" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {CHALLENGES.map(({ en, ja, problemEn, problemJa, solutionEn, solutionJa, lessonEn, lessonJa, accent, iconCls }) => (
            <div key={en} className={cn('bg-white dark:bg-gray-800 rounded-2xl p-7 shadow-sm border-l-4', accent)}>
              <div className="flex items-start gap-3 mb-5">
                <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center shrink-0', iconCls)}>
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white leading-snug">{lang === 'en' ? en : ja}</h3>
                  <p className="text-xs text-gray-400 mt-0.5">{lang === 'en' ? ja : en}</p>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <span className="text-xs font-semibold text-red-500 uppercase tracking-wide">{l.problem}</span>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{lang === 'en' ? problemEn : problemJa}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{lang === 'en' ? problemJa : problemEn}</p>
                </div>
                <div>
                  <span className="text-xs font-semibold text-green-600 uppercase tracking-wide">{l.solution}</span>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{lang === 'en' ? solutionEn : solutionJa}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{lang === 'en' ? solutionJa : solutionEn}</p>
                </div>
                <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{l.lesson}</span>
                  <p className="text-sm text-gray-500 dark:text-gray-400 italic mt-1">
                    "{lang === 'en' ? lessonEn : lessonJa}"
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Section 10: Timeline ──────────────────────────────────────────────────────

const PHASES = [
  { num: '0',  en: 'Environment Setup',                  ja: 'GCP 環境構築・Firestore 設定',       date: '2025-12',    status: 'done'    as const },
  { num: '1',  en: 'FastAPI Foundation',                  ja: 'FastAPI 基盤・データモデル',          date: '2025-12',    status: 'done'    as const },
  { num: '2',  en: 'News Collection — Gemini Grounding',  ja: 'ニュース収集・Gemini 連携',           date: '2026-01',    status: 'done'    as const },
  { num: '3',  en: 'Technical Indicators + Rule Engine',  ja: 'テクニカル指標・ルールエンジン',      date: '2026-01',    status: 'done'    as const },
  { num: '4',  en: 'GMO API + Trade Execution',           ja: 'GMO API・取引実行・リスク管理',       date: '2026-01–02', status: 'done'    as const },
  { num: '5',  en: 'React Dashboard (5 pages)',           ja: 'React ダッシュボード（5ページ）',     date: '2026-01',    status: 'done'    as const },
  { num: '6',  en: 'Cloud Run Deploy + Scheduler',        ja: 'Cloud Run デプロイ・Scheduler 設定', date: '2026-02',    status: 'done'    as const },
  { num: '7',  en: 'Production Stabilization',            ja: '本番稼働・安定化・バグ修正',          date: '2026-02 〜', status: 'active'  as const },
  { num: '8–', en: 'BigQuery Analytics + CI/CD',          ja: 'BigQuery 分析・CI/CD・X 投稿',       date: 'Planned',    status: 'pending' as const },
]

function TimelineSection() {
  const lang = useLang()
  const l = L[lang]
  return (
    <section id="timeline" className="py-24 bg-white dark:bg-gray-950 px-6">
      <div className="max-w-3xl mx-auto">
        <SectionHeader en="Development Journey" ja="開発の歩み" />
        <div className="relative">
          <div className="absolute left-5 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-800" />
          <div className="flex flex-col gap-5">
            {PHASES.map(({ num, en, ja, date, status }) => (
              <div key={num} className="flex gap-5 items-start">
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold shrink-0 z-10 border-2',
                  status === 'done'    && 'bg-green-500 border-green-500 text-white',
                  status === 'active'  && 'bg-blue-500 border-blue-500 text-white',
                  status === 'pending' && 'bg-white dark:bg-gray-950 border-gray-300 dark:border-gray-700 text-gray-400',
                )}>
                  {status === 'done' ? '✓' : status === 'active' ? '▶' : '…'}
                </div>
                <div className="flex-1 bg-gray-50 dark:bg-gray-900 rounded-xl px-5 py-4">
                  <div className="flex justify-between items-start flex-wrap gap-2">
                    <div>
                      <span className="text-xs text-gray-400 font-medium">{l.phase} {num}</span>
                      <h4 className="font-semibold text-gray-900 dark:text-white mt-0.5">{lang === 'en' ? en : ja}</h4>
                      <p className="text-xs text-gray-400">{lang === 'en' ? ja : en}</p>
                    </div>
                    <span className={cn(
                      'text-xs px-2.5 py-1 rounded-full shrink-0 font-medium',
                      status === 'done'    && 'bg-green-100 text-green-700',
                      status === 'active'  && 'bg-blue-100 text-blue-700',
                      status === 'pending' && 'bg-gray-100 dark:bg-gray-800 text-gray-500',
                    )}>
                      {status === 'pending' ? (lang === 'en' ? 'Planned' : '未着手') : date}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Section 11: Next Steps ────────────────────────────────────────────────────

const NEXT_PHASES = [
  { num: '1', en: 'Tick Data Preprocessing',   ja: 'Tickデータ前処理・特徴量生成',      status: 'inProgress' as const, accent: 'border-blue-500' },
  { num: '2', en: 'Meta-Labeling + Backtest',  ja: 'メタラベリング・バックテスト',      status: 'planned'    as const, accent: 'border-slate-600' },
  { num: '3', en: 'GCP Infrastructure',        ja: 'BigQuery / Cloud Run / Vertex AI', status: 'planned'    as const, accent: 'border-slate-600' },
  { num: '4', en: 'Production Trading System', ja: '本番自動売買システム実装',           status: 'planned'    as const, accent: 'border-slate-600' },
]

const NEW_FEATURES = [
  { en: 'VWAP + Volume Imbalance',          ja: 'VWAP + 出来高不均衡（imbalance）' },
  { en: 'Shannon Entropy',                  ja: 'シャノンエントロピー' },
  { en: 'Tick → 1-min OHLCV aggregation',  ja: 'Tick → 1分足 OHLCV 集計' },
  { en: 'BTC/JPY (not FX)',                 ja: 'BTC/JPY（FXではなく暗号資産）' },
  { en: 'Backtest-validated thresholds',    ja: 'バックテストで検証済みの閾値' },
]

function NextStepsSection() {
  const lang = useLang()
  const l = L[lang]
  return (
    <section id="nextsteps" className="py-24 bg-slate-900 text-white px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeader en={l.nextTitle} ja={l.nextSub} light />

        <div className="max-w-2xl mx-auto text-center mb-12">
          <p className="text-slate-400 leading-relaxed">{l.nextDesc}</p>
          <p className="text-slate-600 text-sm mt-3">{l.nextDescSub}</p>
        </div>

        <div className="rounded-2xl border border-slate-700 bg-slate-800 p-8 mb-10">
          <div className="flex items-start gap-4">
            <div className="bg-indigo-600 rounded-xl w-12 h-12 flex items-center justify-center shrink-0">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold mb-1">fx-insight-bot-2nd</h3>
              <p className="text-slate-400 text-sm mb-8">
                BTC/JPY Tick data · Technical Indicators × Machine Learning · Meta-Labeling
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-4">{l.strategyTitle}</p>
                  <div className="flex flex-col gap-2">
                    <div className="bg-slate-700 rounded-xl px-4 py-3">
                      <span className="text-xs text-slate-400">{l.layer1}</span>
                      <p className="text-white font-semibold mt-0.5">Technical Indicators (RSI, MACD)</p>
                      <p className="text-slate-500 text-xs mt-0.5">{l.layer1desc}</p>
                    </div>
                    <div className="flex justify-center text-slate-600 text-sm">↓</div>
                    <div className="bg-slate-700 rounded-xl px-4 py-3">
                      <span className="text-xs text-slate-400">{l.layer2}</span>
                      <p className="text-white font-semibold mt-0.5">ML Model (meta-labeling)</p>
                      <p className="text-slate-500 text-xs mt-0.5">{l.layer2desc}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-4">{l.lotControl}</p>
                  <div className="flex flex-col gap-2 mb-6">
                    {[
                      { confKey: 'lowConf',  lot: `0 — ${l.lotSkip}`,   cls: 'text-slate-500' },
                      { confKey: 'medConf',  lot: '500 / 1,000 units',  cls: 'text-blue-400' },
                      { confKey: 'highConf', lot: '1,500 units',         cls: 'text-indigo-400' },
                    ].map(({ confKey, lot, cls }) => (
                      <div key={confKey} className="flex justify-between bg-slate-700 rounded-lg px-4 py-2.5 text-xs">
                        <span className="text-slate-400">{l[confKey as keyof typeof l]}</span>
                        <span className={cn('font-semibold', cls)}>{lot}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{l.newFeatures}</p>
                  <div className="flex flex-col gap-1.5 text-xs text-slate-400">
                    {NEW_FEATURES.map(({ en, ja }) => (
                      <div key={en} className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                        {lang === 'en' ? en : ja}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {NEXT_PHASES.map(({ num, en, ja, status, accent }) => (
            <div key={num} className={cn('rounded-xl border-l-4 bg-slate-800 border border-slate-700 p-5', accent)}>
              <p className="text-xs text-slate-500 mb-1">{l.phase} {num}</p>
              <h4 className="font-semibold text-white text-sm mb-1">{lang === 'en' ? en : ja}</h4>
              <p className="text-xs text-slate-500 mb-3">{lang === 'en' ? ja : en}</p>
              <span className="text-xs text-slate-400">
                {status === 'inProgress' ? l.inProgress : l.planned}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Language toggle ───────────────────────────────────────────────────────────

function LangToggle({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  return (
    <button
      onClick={() => setLang(lang === 'en' ? 'ja' : 'en')}
      className="fixed top-5 left-5 z-50 flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-bold shadow-lg bg-slate-900/80 backdrop-blur-sm border border-slate-700/60 text-white hover:bg-slate-800 transition-colors"
      title={lang === 'en' ? '日本語に切り替え' : 'Switch to English'}
    >
      <span className="text-base leading-none">{lang === 'en' ? '🇯🇵' : '🇺🇸'}</span>
      {lang === 'en' ? '日本語' : 'English'}
    </button>
  )
}

// ─── Side navigation dots ──────────────────────────────────────────────────────

function SideNav({ active, lang }: { active: string; lang: Lang }) {
  return (
    <nav className="fixed right-5 top-1/2 -translate-y-1/2 z-50 flex-col gap-2.5 hidden lg:flex">
      {SECTIONS.map(({ id, labelEn, labelJa }) => (
        <a
          key={id}
          href={`#${id}`}
          title={lang === 'en' ? labelEn : labelJa}
          className={cn(
            'w-2.5 h-2.5 rounded-full transition-all duration-200 block',
            active === id
              ? 'bg-blue-500 scale-125 ring-2 ring-blue-300 ring-offset-2 ring-offset-transparent'
              : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-500 dark:hover:bg-gray-400',
          )}
        />
      ))}
    </nav>
  )
}

// ─── Page root ─────────────────────────────────────────────────────────────────

export function PresentationPage() {
  const [lang, setLang] = useState<Lang>('en')
  const [activeSection, setActiveSection] = useState('hero')

  useEffect(() => {
    const handleScroll = () => {
      // 画面上部から30%の位置をトリガーラインとして使う
      const triggerY = window.scrollY + window.innerHeight * 0.3
      let current = SECTIONS[0].id
      for (const { id } of SECTIONS) {
        const el = document.getElementById(id)
        if (el && el.offsetTop <= triggerY) current = id
      }
      setActiveSection(current)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll() // 初期状態を設定
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <LangContext.Provider value={lang}>
      <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-white scroll-smooth">
        <LangToggle lang={lang} setLang={setLang} />
        <SideNav active={activeSection} lang={lang} />
        <HeroSection />
        <MotivationSection />
        <FeaturesSection />
        <ArchitectureSection />
        <DataFlowSection />
        <TechStackSection />
        <SignalSection />
        <CostSection />
        <ChallengesSection />
        <TimelineSection />
        <NextStepsSection />
      </div>
    </LangContext.Provider>
  )
}
