# HRM — 人事管理システム

社員の勤怠・給与・目標管理・採用・資産・AI支援などを一元化する社内向け Web アプリケーションです。

---

## 機能一覧

### 全社員向け

| 画面 | 概要 |
|---|---|
| **ダッシュボード** | 出退勤ボタン・KPI・TODO・最新記事・通知を一覧表示 |
| **出退勤管理** | 打刻・前後月切替・プロジェクト別管理・XLSX/CSV/PDF エクスポート・一括アップロード・**36協定状況ダッシュボード**（管理職以上） |
| **有給・休暇** | 有給申請・承認・残日数管理（6種類の休暇タイプ） |
| **目標管理／月報** | MBO 目標設定（上期/下期）・承認フロー・月報作成・日報 |
| **給与明細** | 全支給/控除項目表示・XLSX/PDF ダウンロード |
| **経費申請** | 交通費・経費申請・勘定科目管理・領収書 OCR（AI） |
| **取得資格登録** | スキル・資格登録（レベル文字列・主催者・有効期限アラート） |
| **電子稟議** | 購買・出張などの申請フロー |
| **チャット** | DM・グループチャット・ファイル添付 |
| **360度評価** | 相互評価・評価期間管理 |
| **研修・e-Learning** | コース管理・受講記録・理解度テスト |
| **TODO** | 未着手/作業中/完了のステータス管理・日報 |
| **イントラ** | 記事作成（リッチテキスト/MD/HTML）・承認公開・既読管理 |
| **通知** | システム通知・残業アラート・資格期限警告・ストレスチェック等 |
| **ドキュメント管理** | 雇用契約書・規程・資格証明書をバージョン管理付きで保管 |
| **ストレスチェック** | 厚労省標準 57 問・高ストレス判定・集団分析 |
| **オンボーディング** | 入社手続きタスクのテンプレート管理・進捗トラッキング |
| **AIアシスタント** | HRデータ自然言語照会・MBO目標下書き・日報下書き・領収書 OCR |

### 管理職以上

| 画面 | 概要 |
|---|---|
| **社員情報** | 社員一覧・詳細・緊急連絡先・住所・勤務先・アバター・CSV一括登録 |
| **組織図** | 部署別カード・上下関係ツリー・詳細パネル（アバター付き） |
| **資産管理** | PC・スマホ・備品の台帳管理・貸出・返却・CSV一括登録 |

### 人事・管理者向け

| 画面 | 概要 |
|---|---|
| **採用管理** | 求人票・応募者・面接スケジュール管理 |
| **分析ダッシュボード** | 勤怠・給与・評価などのデータ分析 |
| **給与計算** | 全社員の給与明細計算・手動修正（経理も可） |

---

## 技術スタック

### フロントエンド

| 技術 | 役割 |
|---|---|
| **Next.js 14** (App Router) | React フレームワーク |
| **TypeScript 5** | 型安全な JavaScript |
| **Tailwind CSS** | ユーティリティファースト CSS |
| **Zustand** | グローバル状態管理（認証情報など） |
| **TanStack Query v5** | サーバーデータキャッシュ・同期 |
| **Axios** | HTTP クライアント（JWT 自動付与・401 リフレッシュ） |
| **Tiptap** | リッチテキストエディタ（イントラ記事） |
| **lucide-react** | アイコンライブラリ |

### バックエンド

| 技術 | 役割 |
|---|---|
| **Django 5** | Python Web フレームワーク |
| **Django REST Framework** | REST API 構築 |
| **SimpleJWT** | JWT 認証トークン管理 |
| **drf-spectacular** | Swagger / OpenAPI ドキュメント自動生成 |
| **Anthropic SDK** | Claude AI 連携（tool_use エージェント含む） |
| **openpyxl** | Excel (XLSX) 出力（給与明細・勤怠テンプレート） |
| **reportlab** | PDF 生成（給与明細・勤怠表） |
| **Pillow** | 画像処理（アバター） |

### インフラ・データストア

| 技術 | 用途 |
|---|---|
| **PostgreSQL 16** | メインデータベース |
| **Docker Compose** | ローカル開発環境（DB + Backend + Frontend） |
| **AWS S3** | ファイルストレージ（本番環境） |

---

## ディレクトリ構成

```
HRM/
├── backend/
│   ├── apps/
│   │   ├── accounts/         # ユーザー認証・ロール管理（7 ロール）
│   │   ├── employees/        # 社員情報・緊急連絡先・家族構成・組織図
│   │   ├── attendance/       # 出退勤・プロジェクト管理・36協定アラート
│   │   ├── leave/            # 有給・休暇申請（6種類）
│   │   ├── mbo/              # MBO 目標・月報・日報
│   │   ├── salary/           # 給与明細・等級・手当マスタ
│   │   ├── expense/          # 経費申請・勘定科目
│   │   ├── skills/           # スキル・取得資格（有効期限アラート）
│   │   ├── approval/         # 電子稟議（テンプレート・承認ルート）
│   │   ├── chat/             # DM・グループチャット・添付ファイル
│   │   ├── evaluation/       # 360度評価・評価期間
│   │   ├── learning/         # 研修コース・受講記録・テスト
│   │   ├── recruitment/      # 採用管理・求人・面接
│   │   ├── assets/           # 資産管理（台帳・貸出・返却）
│   │   ├── todo/             # TODO 管理・日報
│   │   ├── intra/            # 社内記事（承認フロー・既読管理）
│   │   ├── notifications/    # 通知（9 タイプ）
│   │   ├── analytics/        # 分析ダッシュボード
│   │   ├── ai_assistant/     # AI 機能（日報・MBO・OCR・HRクエリ）
│   │   ├── onboarding/       # オンボーディング管理
│   │   ├── documents/        # ドキュメント管理（バージョン管理付き）
│   │   ├── stress_check/     # ストレスチェック（57 問・集団分析）
│   │   └── common/           # 共通基盤（SoftDelete・AuditLog）
│   ├── config/               # Django 設定・URL ルーティング
│   └── template/             # OC 作業表テンプレート (XLSX)
├── frontend/
│   └── src/app/(main)/
│       ├── page.tsx           # ダッシュボード
│       ├── attendance/        # 出退勤管理（36 協定タブ含む）
│       ├── employees/         # 社員情報・組織図
│       ├── mbo/               # 目標管理／月報
│       ├── salary/            # 給与明細・給与計算
│       ├── expense/           # 経費申請
│       ├── skills/            # 取得資格登録
│       ├── leave/             # 有給・休暇
│       ├── approval/          # 電子稟議
│       ├── chat/              # チャット
│       ├── evaluation/        # 360度評価
│       ├── learning/          # 研修・e-Learning
│       ├── recruitment/       # 採用管理
│       ├── assets/            # 資産管理
│       ├── todo/              # TODO
│       ├── intra/             # イントラ
│       ├── notifications/     # 通知
│       ├── analytics/         # 分析ダッシュボード
│       ├── ai/                # AI アシスタント（4 タブ）
│       ├── onboarding/        # オンボーディング
│       ├── documents/         # ドキュメント管理
│       ├── stress-check/      # ストレスチェック
│       └── settings/          # 設定（API キー管理など）
└── docker-compose.yml
```

---

## ロール・権限

| ロール | 説明 | 主な権限 |
|---|---|---|
| `customer` | 取引先・顧客 | イントラ閲覧・通知のみ |
| `employee` | 一般社員 | 自身のデータ入力・申請 |
| `supervisor` | 係長・チームリーダー | 部下の閲覧・承認 |
| `manager` | 課長・部長 | 部下の閲覧・承認・勤怠確認 |
| `accounting` | 経理担当 | 給与計算・経費承認 |
| `hr` | 人事担当 | 社員情報管理・採用・分析・全データ閲覧 |
| `admin` | システム管理者 | 全権限・Django 管理サイト |

---

## 共通設計パターン

### 論理削除（SoftDelete）

全モデルが `SoftDeleteModel` を継承。削除は `is_deleted=True` に変更するだけで物理削除しない。
社員削除時は関連する全データ（勤怠・給与・評価・申請等）もカスケード論理削除される。

```python
Model.objects        # 削除済みを除外（通常クエリ）
Model.all_objects    # 削除済みを含む全件
instance.soft_delete(user=request.user)
instance.restore()
```

### 監査ログ（AuditLog）

全 CREATE / UPDATE / DELETE / RESTORE 操作を `AuditLog` に自動記録（誰がいつ何を）。

### 通知

```python
Notification.send(user, type_, title, message, related_url='')
```

対応タイプ: `attendance_mod` / `leave_request` / `mbo_feedback` / `expense_request` / `overtime_alert` / `overtime_annual_alert` / `leave_alert` / `skill_expiry` / `stress_check` / `onboarding` / `system`

---

## ローカル開発環境のセットアップ

### 前提条件

- Docker Desktop がインストールされていること

### 起動手順

```bash
# 1. リポジトリをクローン
git clone <repo-url>
cd HRM

# 2. 環境変数ファイルを作成
cp backend/.env.example backend/.env
# backend/.env を編集して必要な値を設定

# 3. コンテナを起動
docker compose up -d

# 4. マイグレーションを実行
docker compose exec backend python manage.py migrate

# 5. スーパーユーザーを作成（初回のみ）
docker compose exec backend python manage.py createsuperuser

# 6. ブラウザでアクセス
#   フロントエンド: http://localhost:3000
#   API ドキュメント: http://localhost:8000/api/docs/
#   管理サイト:      http://localhost:8000/admin/
```

### 開発時の便利コマンド

```bash
# ログを確認
docker compose logs -f backend
docker compose logs -f frontend

# マイグレーションファイル生成
docker compose exec backend python manage.py makemigrations

# マイグレーション適用
docker compose exec backend python manage.py migrate

# Django シェル
docker compose exec backend python manage.py shell

# フロントエンドの依存関係を更新（package.json 変更後）
docker compose restart frontend
```

---

## 環境変数

`backend/.env.example` をコピーして `backend/.env` を作成してください。

### 必須設定

| 変数 | 説明 |
|---|---|
| `DJANGO_SECRET_KEY` | Django 秘密鍵（本番は長いランダム文字列） |
| `DJANGO_DEBUG` | 本番は `False` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | PostgreSQL 接続情報 |
| `CORS_ALLOWED_ORIGINS` | フロントエンドの URL（例: `http://localhost:3000`） |

### AI 機能設定

| 変数 | 説明 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API キー（Claude AI 機能全般） |

ユーザーごとに個別キーを設定できます（設定画面 → API キー管理）。個別キーが優先されます。

### AWS 連携設定（オプション）

| 変数 | 説明 |
|---|---|
| `AWS_REGION` | AWS リージョン（例: `ap-northeast-1`） |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS 認証情報 |
| `S3_STORAGE_BUCKET` | S3 バケット名（ファイルストレージ本番用） |

---

## 主要 API エンドポイント

| パス | 説明 |
|---|---|
| `POST /api/v1/auth/login/` | ログイン（JWT 発行） |
| `POST /api/v1/auth/refresh/` | トークンリフレッシュ |
| `GET/POST /api/v1/employees/` | 社員一覧・作成 |
| `GET /api/v1/employees/org-chart/` | 組織図データ（アバター・等級付き） |
| `POST /api/v1/attendance/clock-in/` | 出勤打刻 |
| `POST /api/v1/attendance/clock-out/` | 退勤打刻（36 協定アラート自動チェック） |
| `GET /api/v1/attendance/summary/` | 月間勤怠サマリー |
| `GET /api/v1/attendance/overtime-dashboard/` | 全社員 36 協定状況（管理職以上） |
| `GET /api/v1/attendance/csv-export/` | CSV エクスポート |
| `GET /api/v1/attendance/pdf-export/` | PDF エクスポート |
| `POST /api/v1/salary/payslips/calculate/` | 給与計算（人事のみ） |
| `GET /api/v1/notifications/` | 通知一覧 |
| `POST /api/v1/ai/draft-daily-report/` | AI 日報下書き |
| `POST /api/v1/ai/draft-mbo-report/` | AI MBO月報下書き |
| `POST /api/v1/ai/draft-mbo-goal/` | AI MBO目標案生成 |
| `POST /api/v1/ai/analyze-receipt/` | 領収書 OCR |
| `POST /api/v1/ai/hr-query/` | HR 自然言語クエリ（人事のみ） |
| `GET/POST /api/v1/onboarding/templates/` | オンボーディングテンプレート |
| `POST /api/v1/onboarding/assignments/assign/` | 社員へのアサイン |
| `GET/POST /api/v1/documents/` | ドキュメント一覧・作成 |
| `POST /api/v1/documents/{id}/upload/` | ファイルアップロード（新バージョン） |
| `GET /api/v1/documents/{id}/download/` | ファイルダウンロード |
| `GET/POST /api/v1/stress-check/periods/` | ストレスチェック期間管理 |
| `POST /api/v1/stress-check/periods/{id}/publish/` | 公開（全社員に通知） |
| `GET /api/v1/stress-check/periods/{id}/group-analysis/` | 集団分析（人事のみ） |
| `POST /api/v1/stress-check/responses/start/` | 回答開始 |
| `POST /api/v1/stress-check/responses/{id}/submit/` | 最終提出・スコア計算 |
| `GET /api/v1/health/` | ヘルスチェック |
| `GET /api/docs/` | Swagger UI（全 API ドキュメント） |

---

## 主要モデル

```
accounts.User                メールアドレス認証・7 ロール管理
employees.Employee           社員情報（住所・銀行口座・緊急連絡先・家族・アバター）
attendance.AttendanceRecord  勤怠記録（出退勤時刻・プロジェクト・残業計算）
attendance.Project           プロジェクト（件番・名称・管理者）
salary.Payslip               給与明細（支給13項目・控除13項目）
mbo.MBOGoal                  MBO 目標（上期/下期・ウェイト・達成水準）
leave.LeaveRequest           有給・休暇申請（6種類）
expense.ExpenseRequest       経費申請
approval.ApprovalRequest     電子稟議申請
chat.ChatRoom                チャットルーム（DM・グループ）
evaluation.Evaluation360     360 度評価
learning.LearningCourse      研修コース・テスト
recruitment.Candidate        採用応募者
assets.Asset                 社内資産（台帳）
skills.Skill                 スキル・資格
notifications.Notification   通知（9 タイプ）
onboarding.OnboardingTemplate         オンボーディングテンプレート
onboarding.OnboardingAssignment       社員へのアサイン
documents.Document           ドキュメント（バージョン管理付き）
stress_check.StressCheckPeriod        ストレスチェック実施期間
stress_check.StressCheckResponse      回答・スコア（57問・高ストレス判定）
common.AuditLog              全操作ログ（誰がいつ何を）
```

---

## 開発メモ

- **論理削除**: 全モデルで `is_deleted` フラグによる論理削除を採用。物理削除は原則禁止
- **社員削除**: 社員を削除すると勤怠・給与・評価など全関連データが連動して論理削除される
- **AI 機能**: Claude Sonnet 4.6（HRクエリ）と Haiku 4.5（下書き・OCR）を用途別に使い分け
- **36協定閾値**: 月 45h（警告）/ 60h（超過）、年 320h（警告）/ 360h（超過）
- **ストレスチェック**: スコア 77 点以上を高ストレスと判定（逆転項目を考慮した加算方式）
- **OC作業表テンプレート**: `backend/template/OC作業表（名前）2026年度.xlsx` を XLSX エクスポートのベースとして使用
- **Swagger UI**: 開発中は `http://localhost:8000/api/docs/` で全 API を確認可能
