# HRM — 人事管理システム

社員の勤怠・給与・目標管理・スキル管理を一元化する社内向け Web アプリケーションです。

---

## 機能一覧

| 画面 | 概要 |
|---|---|
| ダッシュボード | 出退勤ボタン・KPI・TODO・最新記事・通知を一覧表示 |
| 出退勤管理 | 打刻・前後月切替・プロジェクト別管理・XLSX/CSV/PDF エクスポート・アップロード |
| 社員情報 | 社員一覧・詳細・緊急連絡先・住所・勤務先・アバター画像・組織図 |
| 目標管理／月報 | MBO 目標設定（上期/下期）・承認フロー・月報作成 |
| 給与明細 | 全支給/控除項目表示・XLSX/PDF ダウンロード・人事担当者による計算・修正 |
| 経費申請 | 交通費・経費申請・勘定科目管理 |
| 取得資格登録 | スキル・資格登録（レベル文字列・主催者・有効期限アラート） |
| 有給・休暇 | 有給申請・承認・残日数管理 |
| イントラ | 記事作成（リッチテキスト/MD/HTML）・承認公開・既読管理 |
| TODO | 未着手/作業中/完了のステータス管理 |
| 通知 | システム通知・残業アラート・資格期限警告 |

---

## 技術スタック

### フロントエンド

| 技術 | バージョン | 役割 |
|------|-----------|------|
| **Next.js** | 14.2.3 | React フレームワーク（App Router） |
| **TypeScript** | 5 | 型安全な JavaScript |
| **Tailwind CSS** | 最新 | ユーティリティファースト CSS |
| **shadcn/ui** | 最新 | UI コンポーネントライブラリ |
| **Zustand** | 4.5.2 | グローバル状態管理 |
| **TanStack Query** | 5.40.0 | サーバーデータキャッシュ・同期 |
| **React Hook Form** | 7.52.0 | フォーム管理・バリデーション |
| **Tiptap** | 3.22.3 | リッチテキストエディタ |
| **Axios** | 1.7.2 | HTTP クライアント |
| **Zod** | 最新 | スキーマバリデーション |

### バックエンド

| 技術 | バージョン | 役割 |
|------|-----------|------|
| **Django** | 5.0.4 | Python Web フレームワーク |
| **Django REST Framework** | 3.15.1 | REST API 構築 |
| **SimpleJWT** | 5.3.1 | JWT 認証トークン管理 |
| **drf-spectacular** | 0.27.2 | Swagger / OpenAPI ドキュメント自動生成 |
| **Celery** | 5.3.6 | 非同期タスクキュー（メール送信・PDF生成など） |
| **Redis** | 5.0.4 | キャッシュ・Celery タスクブローカー |
| **openpyxl** | 3.1.2 | Excel (XLSX) 出力 |
| **reportlab** | 4.1.0 | PDF 生成 |
| **boto3** | 1.34.84 | AWS SDK |
| **Pillow** | 10.3.0 | 画像処理（アバター） |

### インフラ・データストア

| 技術 | 用途 |
|------|------|
| **PostgreSQL 16** | メインデータベース |
| **Redis** | キャッシュ・Celery ブローカー |
| **Docker Compose** | ローカル開発環境 |
| **AWS S3** | ファイルストレージ（本番） |
| **AWS Bedrock** | AI 機能（MBO フィードバック） |
| **AWS Cognito** | 外部認証（オプション） |

---

## ディレクトリ構成

```
HRM/
├── backend/                  # Django REST API
│   ├── apps/
│   │   ├── accounts/         # ユーザー認証・ロール管理
│   │   ├── employees/        # 社員情報・緊急連絡先・家族構成
│   │   ├── attendance/       # 出退勤・プロジェクト管理
│   │   ├── leave/            # 有給・休暇申請
│   │   ├── mbo/              # 目標管理・月報・日報
│   │   ├── salary/           # 給与明細・等級マスタ・手当
│   │   ├── expense/          # 経費申請・勘定科目
│   │   ├── skills/           # スキル・取得資格
│   │   ├── notifications/    # 通知
│   │   ├── todo/             # TODO 管理
│   │   └── intra/            # 社内記事（イントラネット）
│   ├── config/               # Django 設定・URL
│   └── template/             # OC作業表テンプレート (XLSX)
├── frontend/                 # Next.js App Router
│   └── src/app/(main)/
│       ├── page.tsx          # ダッシュボード
│       ├── attendance/       # 出退勤管理
│       ├── employees/        # 社員情報・組織図
│       ├── mbo/              # 目標管理／月報
│       ├── salary/           # 給与明細
│       ├── expense/          # 経費申請
│       ├── skills/           # 取得資格登録
│       ├── leave/            # 有給・休暇
│       ├── intra/            # イントラ
│       ├── todo/             # TODO
│       └── notifications/    # 通知
├── docker-compose.yml
└── template/                 # CSV アップロードテンプレート
```

---

## ロール・権限

| ロール | 権限 |
|---|---|
| `employee`（社員） | 自身の打刻・申請・目標入力・スキル登録 |
| `manager`（管理職） | 部下の閲覧・承認・目標フィードバック |
| `hr`（人事担当） | 社員情報管理・給与計算・勤怠集計・経費承認 |
| `admin`（システム管理者） | アカウント作成・権限管理・マスタ管理 |

---

## ローカル開発環境のセットアップ

### 前提条件

- Docker Desktop がインストールされていること
- Node.js 18 以上（フロントエンドを Docker 外で動かす場合）

### 起動手順

```bash
# 1. リポジトリをクローン
git clone <repo-url>
cd HRM

# 2. コンテナを起動
docker compose up -d

# 3. マイグレーションを実行
docker compose exec backend python manage.py migrate

# 4. スーパーユーザーを作成（初回のみ）
docker compose exec backend python manage.py createsuperuser

# 5. ブラウザでアクセス
#   フロントエンド: http://localhost:3000
#   バックエンド API: http://localhost:8000
#   API ドキュメント: http://localhost:8000/api/docs/
#   管理サイト: http://localhost:8000/admin/
```

### 開発時の便利コマンド

```bash
# バックエンドのログを確認
docker compose logs -f backend

# マイグレーションファイル生成
docker compose exec backend python manage.py makemigrations

# マイグレーション適用
docker compose exec backend python manage.py migrate

# Django シェル
docker compose exec backend python manage.py shell

# フロントエンドの依存関係インストール（パッケージ追加後）
docker compose restart frontend
```

---

## 環境変数

`backend/.env.example` をコピーして `backend/.env` を作成してください。  
本番環境では以下を必ず変更してください。

### 必須設定

| 変数 | 説明 |
|------|------|
| `DJANGO_SECRET_KEY` | Django 秘密鍵（本番は長いランダム文字列） |
| `DJANGO_DEBUG` | 本番は `False` に設定 |
| `DB_PASSWORD` | PostgreSQL パスワード |
| `CORS_ALLOWED_ORIGINS` | フロントエンドの本番 URL |

### AWS 連携設定（オプション）

| 変数 | 説明 |
|------|------|
| `AWS_REGION` | AWS リージョン（例: `ap-northeast-1`） |
| `AWS_ACCESS_KEY_ID` | AWS アクセスキー |
| `AWS_SECRET_ACCESS_KEY` | AWS シークレットキー |
| `S3_STORAGE_BUCKET` | S3 バケット名（ファイルストレージ） |
| `BEDROCK_MODEL_ID` | Bedrock モデル ID（AI 機能） |
| `COGNITO_USER_POOL_ID` | Cognito ユーザープール ID（外部認証） |
| `COGNITO_APP_CLIENT_ID` | Cognito アプリクライアント ID |

---

## API エンドポイント一覧

| パス | 説明 |
|---|---|
| `POST /api/v1/auth/login/` | ログイン（JWT 発行） |
| `POST /api/v1/auth/refresh/` | トークンリフレッシュ |
| `GET/POST /api/v1/employees/` | 社員一覧・作成 |
| `GET/PATCH /api/v1/employees/{id}/` | 社員詳細・更新 |
| `POST /api/v1/employees/{id}/upload-avatar/` | アバター画像アップロード |
| `GET /api/v1/employees/org-chart/` | 組織図データ |
| `POST /api/v1/attendance/clock-in/` | 出勤打刻 |
| `POST /api/v1/attendance/clock-out/` | 退勤打刻 |
| `GET /api/v1/attendance/template/` | XLSX テンプレートダウンロード |
| `GET /api/v1/attendance/csv-export/` | CSV エクスポート |
| `GET /api/v1/attendance/pdf-export/` | PDF エクスポート |
| `POST /api/v1/attendance/upload/` | XLSX/CSV アップロード |
| `GET/POST /api/v1/attendance/projects/` | プロジェクト一覧・作成 |
| `POST /api/v1/salary/payslips/calculate/` | 給与計算（人事のみ） |
| `GET /api/v1/salary/payslips/{id}/download/` | 給与明細 XLSX |
| `GET /api/v1/salary/payslips/{id}/download-pdf/` | 給与明細 PDF |
| `PATCH /api/v1/salary/payslips/{id}/update/` | 給与明細手動修正（人事のみ） |
| `GET /api/v1/skills/` | スキル・資格一覧 |
| `GET /api/v1/mbo/goals/` | MBO 目標一覧 |
| `GET /api/v1/intra/articles/` | イントラ記事一覧 |
| `GET /api/v1/intra/articles/recent/` | 最新記事（ダッシュボード用） |
| `GET /api/v1/todo/items/` | TODO 一覧 |
| `GET /api/v1/notifications/` | 通知一覧 |
| `GET /api/v1/health/` | ヘルスチェック |
| `GET /api/docs/` | Swagger UI（API ドキュメント） |

---

## 主要モデル

```
accounts.User           メールアドレス認証・ロール管理
employees.Employee      社員情報（住所・銀行口座・緊急連絡先・家族）
attendance.Project      プロジェクト（件番・名称・管理者）
attendance.AttendanceRecord  勤怠記録（出退勤時刻・プロジェクト・残業）
salary.SalaryGrade      給与等級マスタ
salary.Allowance        手当マスタ（技術・住宅・通勤など12種）
salary.Payslip          給与明細（支給13項目・控除13項目・勤怠・管理情報）
mbo.MBOGoal             MBO 目標（上期/下期・ウェイト・達成水準）
mbo.MBOReport           月報（目標進捗・上司コメント）
skills.Skill            スキル・資格（レベル文字列・主催者・有効期限）
intra.Article           イントラ記事（承認フロー・既読管理）
expense.ExpenseRequest  経費申請
leave.LeaveRequest      有給・休暇申請
todo.TodoItem           TODO（未着手/作業中/完了）
notifications.Notification  通知
```

---

## 開発メモ

- **マイグレーション**: Docker を使わずに手動作成した migration ファイルは `backend/apps/*/migrations/` に格納
- **OC作業表テンプレート**: `backend/template/OC作業表（名前）2026年度.xlsx` を XLSX エクスポートのベースとして使用
- **Swagger UI**: 開発中は `http://localhost:8000/api/docs/` で全 API を確認可能
- **管理サイト**: `http://localhost:8000/admin/` — システム管理者がログイン可能
