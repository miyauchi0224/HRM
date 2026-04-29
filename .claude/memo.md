# 実装完了事項（2026-04-29）

## カレンダー機能 - DB永続化・エクスポート・ローカル保存対応

### バックエンド（calendar_sync/views.py）
- ✅ `events()` エンドポイント：DB保存済みイベント + 外部カレンダー（MS/Google）をマージして返却
- ✅ `create_event()` 修正：
  - provider='local'/'ms'/'google' の3パターンに対応
  - DB に CalendarEvent を保存
  - provider指定時は optional で外部カレンダー同期（同期未設定でも DB保存は成功）
- ✅ `update_event()` 修正：
  - DB の CalendarEvent を先に更新
  - 外部カレンダー（external_id 存在時）も更新
  - provider='local' でも動作（DB のみ更新）
- ✅ `delete_event()` 修正：
  - DB から削除（soft delete）
  - 外部カレンダーがあれば同期削除
- ✅ `export_events()` エンドポイント：
  - format=csv または format=ics でエクスポート
  - 年月フィルタリング対応
  - CSV：タイトル, 開始日時, 終了日時, プロバイダー, 作成日
  - ICS：RFC 5545 準拠

### フロントエンド（CalendarPanel.tsx）
- ✅ provider 型を 'ms' | 'google' | 'local' に拡張
- ✅ 新規予定作成時：provider をセレクトボックスで選択（デフォルト='local'）
- ✅ ダブルクリック予定追加：provider選択なし、モーダルで選択
- ✅ イベント色分け：
  - Microsoft: 青（#3b82f6）
  - Google: 紫（#8b5cf6）
  - Local: 緑（#10b981）
- ✅ エクスポート機能：
  - CSV/ICS ボタンを追加（ヘッダー）
  - 年月でフィルタ
  - ブラウザダウンロード実装
- ✅ 凡例にローカルカレンダー追加

## 仕様
- **ローカル保存**: MS/Google 連携なしでも DB にイベント保存可能
- **外部同期オプション**: トークン存在時のみ同期（トークン未設定でも機能停止しない）
- **エクスポート**: 現在表示月のイベントを CSV/ICS で一括ダウンロード

## 実装チェック

### バックエンド
- [x] CalendarEvent モデル（UUID PK, user FK, title, start/end datetime, provider, external_id, url）
- [x] create_event()：DB + optional 外部同期
- [x] update_event()：DB 優先 + external_id 同期
- [x] delete_event()：DB soft delete + external 同期
- [x] events()：DB + MS/Google マージ
- [x] export_events()：CSV/ICS
- [x] oauth_ms_start/callback：Microsoft OAuth
- [x] oauth_google_start/callback：Google OAuth
- [x] oauth_revoke()：連携解除
- [x] tokens()：接続済みプロバイダー一覧

### フロントエンド
- [x] CalendarPanel コンポーネント完全実装
- [x] 祝日表示（赤色）
- [x] 土曜（青色）/日曜（赤色）色分け
- [x] ダブルクリック予定追加
- [x] 予定編集モーダル
- [x] 予定削除確認
- [x] CSV/ICS エクスポート
- [x] OAuth ボタン（MS/Google）
- [x] 連携解除機能
- [x] provider セレクト（local/ms/google）
- [x] 凡例表示

## 動作確認項目
1. マイグレーション実行後、CalendarEvent テーブルが作成されること
2. ローカルで予定を作成→DB に保存される
3. MS/Google トークンがあれば外部カレンダーにも同期される
4. エクスポート：CSV/ICS で現在月のイベントダウンロード
5. 予定編集：DB と外部カレンダー両方更新
6. 予定削除：DB と外部カレンダー両方削除

---

# 人事管理HRM



## ログイン・ログアウト機能
ログインすると、
出退勤打刻可能
今月の勤務リスト表示
TODOリスト表示


## MBO
MBO、上期と下期、目標設定して、達成水準を設定。月間報告で、目標に向けた行動内容と結果結論を記述、上司からの指摘。
印刷：PDF、XLSX
日報

スキル管理


## 組織図
管理者は社員を部下に登録可能。
社員は複数の管理者可能。

###
緊急連絡先（電話番号、続柄、氏名）、電話番号、メールアドレス
経歴
家族構成
（配偶者・扶養家族）



## 出勤退勤打刻
プロジェクト入力（プロジェクト件番、プロジェクト名、プロジェクト管理者）
稼働管理する。
CSV、XLSXでアップロード可能。
テンプレートをダウンロード可能
印刷：PDF、XLSX
カレンダー


## 給与計算機能
基本給（等級）を登録して、
給与計算、
PDFでダウンロード可能
年末調整
PDFでダウンロード可能
住民税、課税・税率？

### 経費申請機能
交通費
経費
勘定科目

### 手当
手当の入力
住宅手当
出向手当
技術手当


## システム仕様
### 権限ロール
社員-プロジェクト従事者
上司-社員の上位者
管理職-取締役や部長・課長など
人事担当者
システム管理者（アカウント作成権限あり）

###
アカウント申請
アカウント発行・承認

###
BE:
Django REST

FE:
next.js
Typescript

DB:
postgres



#
勘定科目はcsvでダウンロード可能
勘定科目はcsでアップロードして更新可能

出退勤のテンプレートをxlsxで作成日までのデータをダウンロード可能
出退勤のテンプレートは年度単位
出退勤のテンプレートをアップロードして、出退勤情報を更新可能
（参考：テンプレートはtemplateフォルダに格納）


#
画面遷移図を設計に追加して

#
マイグレーションファイルを作成して

# ネットワークのログ読み込み
import os
from glob import glob
[os.remove(g) for g in glob(f"localhost.har/*.txt")]
with open("localhost.har.txt","r",encoding="utf-8") as f:
    for i,line in enumerate(f.readlines()):
        fid = int(i//200)
        wfile = f"localhost.har/{fid}.txt"
        with open(wfile,"a",newline="",encoding="utf-8") as fw:
            fw.write(line)



#
重大
JSバンドルが巨大すぎる — main-app.js が 5.74MB はかなり大きい。Code Splitting（コード分割）の余地が大
セキュリティヘッダーが未設定 — Content-Security-Policy・X-Frame-Options 等が全部欠如。本番リリース前に必須
キャッシュ戦略 — 静的アセットも no-store になっており、再訪時に毎回フルロード

パフォーマンス
初期表示に3秒以上 — DOMContentLoaded: 1,023ms / onLoad: 3,044ms。開発環境とはいえ重い
リクエストのキューイング — ブロッキング時間が後のリクエストほど増加している（ブラウザの並行接続数制限に近づいている）

#
勤怠情報をxlsx,CSV,PDFで出力可能。
xlsxのフォーマットはtemplate/OC作業表（名前）2026年度.xlsx
csvまたはxlsxでアップロードして、出退勤情報を登録可能。


# mbo が 404
GET http://localhost:3000/mbo 404 (Not Found)Understand this error
inject.js:77 WARNING:Found both blacklist and siteRules — using siteRules
main-app.js?v=1776070653591:1825 Download the React DevTools for a better development experience: https://reactjs.org/link/react-devtools


# http://localhost:3000/leave　が 404



# 
表示OK


・ mbo
目標登録はデフォルトで上期下期、期間を細分化できる。
目標登録後、上司に依頼送信。

登録した目標は管理職の承認。
承認後、月報作成可能。

月報作成後、社員は申請できる。
申請後に上司は承認できる。


・　給与計算
人事担当者は、締め日を設定できる。
デフォルト：前月16日から15日まで

以下の条件が満たされたとき、給与計算が可能。
　当月の勤務記録があり、勤務記録にはプロジェクト件番があり、プロジェクト名があり、プロジェクト管理者がある。

給与計算の算出は丁寧に出力
給与計算はCSV、xlsx、pdfで出力可能。


以下のイントラ機能を追加機能を設計して、改良を提案して
・ イントラ機能
左メニューにイントラを追加、
社員はイントラに記事を作成（申請）可能。
記事作成ではリンクや画像を張ることができる。
テキスト形式で記述可能。md形式で記述可能。html形式で記述可能。画像アップロード機能を具備。

記事は管理職が承認可能。
記事は承認されると、参照可能状態になる。
ログイン後のダッシュボードに、最近の記事のリンクを5つ掲載。
記事はタイトルがあり、投稿者名があり、承認者がある。
記事の閲覧者（既読ユーザ）を確認できる。



・ TODO機能
TODOには、実施済み、作業中、未着手のグループがあり、必ずどれか一つに属する。
ログイン後のダッシュボードに、TODOリストが表示される。
TODOリストは左メニューから編集可能。




#
社員情報に追加
電話番号

緊急連絡先
氏名：続柄：電話番号

#
・社員情報に住所、郵便番号を追加
・最寄り駅追加
（勤務先の住所・電話番号、勤務先名を追加、通勤経路の候補を提案可能、通勤経路を登録・編集可能）
・MBO
作成中の目標を申請するま編集可能に。
達成水準は定量的に記述するように案内。
ウェイト100%になるまで、申請できない。


・出退勤打刻を出退勤管理に名称変更
・出退勤のエクスポートで、シート一枚目は件番、（Template/OC作業表に厳密に従って）
・出退勤のエクスポートの拡張子をxlsxに変更。
・出退勤のアップロードでエラー
⚠ 一部エラーがあります


新規登録: 0件　更新: 0件

シート「件番」: tuple index out of range
シート「件番」: tuple index out of range
シート「件番」: tuple index out of range
シート「件番」: tuple index out of range


・過去の給与明細を確認可能。CSV、PDFでダウンロード可能。

・過去の経費明細を確認可能。CSV、PDFでダウンロード可能。


・スキル登録を取得資格登録に名称変更
・スキルに有効期限を登録可能。失効していれば、失効と表示。

・役職について
社員は必ず上司が必須。
・役職追加
社員、主任、係長、次長、課長、部長、取締役、社長、副社長


・ダッシュボードにも、出勤、退勤ボタンを実装して

・社員情報の表示でエラー

Unhandled Runtime Error
TypeError: Cannot read properties of undefined (reading 'slice')

Source
src/app/(main)/employees/page.tsx (228:26) @ slice

  226 |       <div className="flex items-center gap-4 p-6 border-b border-gray-100">
  227 |         <div className="w-14 h-14 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xl font-bold shrink-0">
> 228 |           {emp.full_name.slice(0, 1)}
      |                          ^
  229 |         </div>
  230 |         <div>
  231 |           <h2 className="text-xl font-bold text-gray-800">{emp.full_name}</h2>
Call Stack
Show collapsed frames



# ✅ 2026-04-15 給与明細全項目対応
- Employee: 銀行口座フィールド追加（bank_name/branch/type/number/holder）→ migration 0004
- Payslip: 全支給・控除項目追加 → migration 0002_payslip_full_fields
  支給: 技術/出向/住宅/残業/通勤/家族/資格/役職/特別/皆勤/精勤/時間外手当
  控除: 介護保険料/社保合計/財形/社宅寮費/組合費/共済会費/持株会/その他控除
  勤怠: 出勤・欠勤・有給日数、締め日・支給日・備考
- _calculate_payslip: 個別手当マスタから手当種別ごとに自動集計、40歳以上介護保険自動計算
- PATCH /api/v1/salary/payslips/{id}/update/ で人事担当者が個別項目を手動修正可
- XLSX/PDF の両フォーマットで全項目を給与明細書レイアウトで出力
- フロント: 全項目を支給明細・控除明細に分けて表示、XLSX/PDF ダウンロードボタン


# ✅ 2026-04-14 対応済み
- 出退勤エクスポート: xlsx/csv/pdf の拡張子対応済み（OC作業表テンプレート準拠）
- 出退勤アップロード: Excelシリアル日付（整数）を from_excel() で変換、1900年代はスキップ
- 件番シートはアップロード処理でスキップ（OC_SKIP_SHEETS）
- 社員情報ページの full_name.slice エラー修正（null guard追加）
- サイドバー: MBO目標管理 → 目標管理/月報
- スキル: level を文字列フィールドに変更、organizer（主催者）フィールド追加
  → migration: 0002_skill_level_str_organizer.py
- 出退勤管理: 前月・次月ナビゲーション追加
- 出退勤管理: プロジェクトCRUD（作成・編集・削除）フロントエンド実装
  → ProjectViewSet を ReadOnly → ModelViewSet に変更
- 社員: アバター画像アップロード（POST /api/v1/employees/{id}/upload-avatar/）
  → Employee.avatar ImageField 追加、migration: 0003_employee_avatar.py


#
社員アイコンに画像登録可能。アイコンは円形で表示。表示箇所は変更ドラッグで可能。

社員は自分の社員情報を編集可能

出退勤管理は今月のほかに、前月、次月も表示可能。

出退勤管理には労働時間の内訳として、各プロジェクトに使用した時間を記入しなければならない。
プロジェクトには、件番とプロジェクト名とプロジェクト管理者を持つ。
このプロジェクトリストは社員が作成、編集、削除可能。



社員の自スキルの一括登録機能でcsvアップロード可能。

人事職、管理職以上は勘定科目の一括登録ができる。
CSVでアップロード可能。

django管理サイトは管理サイトに名称変更。管理サイトはシステム管理者がログイン可能。

django管理サイトにあるプロジェクト追加・編集機能をフロントエンドの勤怠管理に実装。

MBO目標管理を名称変更、目標管理／月報

スキル登録のレベルは文字列で入力。主催者も入力項目に追加。

#
給与の項目（推奨追加項目含む）
基本給:
技術手当:
出向手当:
住宅手当:
残業手当:
通勤手当（交通費）:
家族手当:
資格手当:
役職手当:
特別手当（賞与・臨時手当）:
皆勤手当:
精勤手当:
時間外手当（深夜・休日など）:
支給合計:
健康保険料:
厚生年金:
雇用保険料:
介護保険料:
社会保険料合計:
財形貯蓄:
社宅・寮費:
組合費:
共済会費:
持株会拠出金:
その他控除（弁当代、貸付金返済など）:
所得税:
住民税:
控除合計:
差引支給額:
勤怠日数（出勤日数、欠勤日数、有給取得日数など）:
締め日・支給日:
支給年月:
社員番号:
部署名:
銀行口座情報（支給先、表示のみ）:
備考欄:


#
目標管理の申請はウェイト100になるまで申請できない。
目標管理の期間は最大で上期、下期の半年間、最小で1か月間。

経費申請は立て替えか先払いか選択可能

TODO機能に日報追加
TODOリストの項目にはプロジェクトを紐づける
TODOリストの項目はドラッグによって未着手と作業中と実施済みを切り替えられる

# 
日報について、別の日も参照・編集・提出できる。

新しい目標を登録するとき、複数の目標を登録可能。
複数の目標のウェイトが合計で100になる。

ダッシュボードの未読通知をクリックすると、通知画面へ移動


TODOをTODO／日報に名称変更
TODO画面は上部にカンバン、下部に日報の画面にする。

管理サイトへのリンクが404


#
顧客追加可能
ロールグループ
社員：
上司：
管理職：
顧客：
人事：
経理：

役職：

画面遷移高速化

#
人事、財務、以上のロールに対して、
給与明細、経費、一括登録機能追加。
一括登録で使用するテンプレート作成。


#
ログイン
利用規約への同意、チェックボックスがデフォルトオフ。
チェックボックスがONでなければ、ログインできない。
チェックボックスがオフでログインすれば、メッセージ表示。
利用規約には、本アプリが※※社の業務情報を持ち、ログインすると機密保持に同意したものとみなす。適切に取り扱う契約に合意。


#

招待メール
通信暗号化

#
このプロジェクトは、間接業務をシステム化します。ほかに追加する良さそうな機能を提案して。

#
稟議は申請者が起案者であり、上司の承認、部門長の承認、財務の承認のフローで、審査中の内訳として表示される。
ユーザのAI利用はユーザのAPI登録が必須で、AIはそのAPIを利用する。
情報機器管理の追加
情報機器の登録、削除、編集、テンプレートCSVからの一括登録、テンプレートCSVからの一括削除、テンプレートCSVのダウンロード、

利用規約の文面を改善して。


360度評価で入力可能。
以下の項目を5段階評価。



① 業務遂行・仕事の進め方

計画性・段取り力
優先順位付けの適切さ
期限・約束の遵守
業務の正確性・丁寧さ
改善提案・工夫の姿勢

日常業務の信頼性を見る項目

② 主体性・自律性

指示待ちにならず行動できる
自分の役割を理解して動いている
課題を自分事として捉えている
困難に直面したときの粘り強さ

若手・研究職・専門職で特に有効

③ 学習姿勢・成長意欲

新しい知識・スキルを学ぶ姿勢
フィードバックを受け入れる態度
自己改善への取り組み
失敗から学ぶ姿勢

人材育成目的の360度評価では重要

④ 対人配慮・感情面（EQ）

他者の立場を考えた対応
感情のコントロール
周囲への気配り
衝突時の冷静さ

チームワーク・職場風土の可視化に役立つ

⑤ チーム・組織への貢献

情報共有の積極性
他メンバーへの支援
チーム全体視点の行動
組織ルール・方針の尊重

個人主義に偏っていないかを見る

⑥ リーダー・管理職向け追加項目

メンバー育成・指導力
公平性（えこひいきしない）
判断力・意思決定の質
責任の取り方
心理的安全性の醸成

部下評価が非常に重要な領域

⑦ 倫理・コンプライアンス

誠実な行動
情報管理・守秘意識
公平性・透明性
ハラスメントを起こさない姿勢

公的機関・研究機関・企業で必須

⑧ 創造性・問題解決（研究・技術系向け）

問題発見力
仮説立案・思考の柔軟性
新しい視点の提示
試行錯誤への前向きさ

研究者・エンジニアに適した評価軸

⑨ 外部対応・社会性（該当者のみ）

外部関係者との対応力
説明の分かりやすさ
調整力・交渉姿勢
組織代表としての振る舞い



# ✅ 2026-04-20 チャット・e-Learning拡張
## チャット添付ファイル
- ChatAttachment モデル追加（chat/models.py）→ migration 0003
- 複数ファイル添付（FormData POST）、合計10MB制限
- 画像: サムネイル表示 (w-40 h-28 object-cover)
- 非画像: ファイル名＋サイズ＋ダウンロードリンク
- 送信前プレビュー（画像は16x16サムネイル、非画像はファイル名）
- 送信者アバター（sender_avatar）もメッセージ表示に対応

## e-Learning ファイル添付
- CourseAttachment モデル追加 → migration 0002
- コース作成モーダルでファイル複数添付可能
- コース詳細にファイルリンク表示

## e-Learning 理解度確認テスト
- Quiz / QuizQuestion / QuizChoice / QuizAttempt / QuizAnswer モデル追加
- Quiz はコースに1対1（OneToOne）
- QuizQuestion: 選択式（choice）・自由記述（free_text）の2種
- 選択式は自動採点（is_correct判定）、自由記述はスコア対象外
- API:
  - GET  /api/v1/learning/courses/{id}/quiz/  → テスト取得
  - POST /api/v1/learning/courses/{id}/quiz/create/  → テスト作成（HR専用）
  - POST /api/v1/learning/quizzes/{id}/questions/   → 問題追加
  - POST /api/v1/learning/quizzes/{id}/start/       → 受験開始
  - POST /api/v1/learning/quizzes/{id}/submit/{attempt_id}/  → 提出・採点
- フロント: テスト受験UI（選択式ラジオ/自由記述テキストエリア）・結果表示（合否・スコア）
- フロント: HR向け問題管理タブ（問題追加・削除）




#
出勤時刻の横に打刻時刻、退勤時刻の横に打刻時刻を表示

#
DBに登録データは削除できない。
DBに登録したデータは非表示にすることができる。
DBにはレコードが追加された時刻を記録する。
これによって、全ユーザの全操作記録をDBから追跡可能。




# ✅ 2026-04-20 論理削除・全操作ログ基盤（ソフトデリート）

## 設計方針
- DBからの物理削除を禁止。全モデルで is_deleted=True による論理削除のみ可能。
- restore() で削除取り消し可能。
- 全操作（作成・更新・削除・復元）を AuditLog テーブルに自動記録。

## 新規 apps/common/
- models.py  — SoftDeleteModel（abstract）+ AuditLog
- mixins.py  — SoftDeleteViewSetMixin（destroy/restoreアクション）
- signals.py — post_saveシグナルで全モデルのCREATE/UPDATEをログ記録
- migrations/0001_initial.py — AuditLogテーブル作成

## SoftDeleteModel の仕様
- 追加フィールド: is_deleted, deleted_at, deleted_by
- Model.objects     → 削除済み除外（通常クエリ）
- Model.all_objects → 削除済みを含む全件（監査・管理用）
- instance.soft_delete(user) → 論理削除
- instance.restore()         → 削除取り消し
- instance.delete()          → 内部でsoft_deleteを呼ぶ（物理削除ブロック）

## 適用済みアプリ（16アプリ / 50+モデル）
employees, attendance, chat, learning, mbo, salary, expense,
todo, intra, evaluation, skills, approval, recruitment, assets, leave, notifications

## マイグレーション適用コマンド
docker compose exec backend python manage.py migrate


docker compose exec backend python manage.py makemaigrations

#
資産管理のCSV一括削除は不要。

社員削除後は、当該社員の情報やアップロードしたデータは全て非表示となる。



＃
ドキュメント管理、ドラッグで持っていける。doc,xls,ppt,pdfなどはサムネイル表示可能。
公開範囲にロール、プロジェクトを追加

電子稟議
起案時に見積書添付。複数添付可。

チャット
既存グループにメンバ追加可能。メンバ削除可能。

経費申請
領収書添付。複数添付可。jpg,png,pdfなどはサムネイル表示。ダウンロード可能。

採用管理
求人一覧で選択すると、求人内容の確認ができる。
応募者の確認ができる。

「プロジェクト管理」画面の追加
プロジェクトの進行度をガントチャートで表示。
作業項目の追加編集可能。
プロジェクトの作業項目はチケット単位。
プロジェクトの作業項目、工程表のテンプレートダウンロード可能で、アップロードで一括登録。

ダッシュボードに自分のプロジェクトのガントチャートを表示


36協定状況
代表者：表示

出退勤管理
勤怠一覧にて、出勤の横に出勤打刻時刻、退勤の横に退勤打刻時刻を表示（編集可能）
退勤の打刻はいつでも打刻可能。
24時でリセット。1日に1回まで出勤打刻可能。出勤打刻されると、退勤打刻をいつでも可能。

資格登録
社外の資格登録には、PDFまたはJPG、PNGなどの添付可能。

社員登録に顧客登録可能
社員登録にメールアドレス、電話番号は必須。

月報に行動内容、結果・考察に追加して「次月の課題」

以下の項目でAIアシスタントによる文章提案
日報。
月報の行動内容、結果・考察、次月の課題。
イントラ記事
目標と達成水準
採用管理の求人



360度評価
評価可能。


ストレスチェック機能 
 GET http://localhost:3000/stress-check/3837a52f-3de1-4b10-a4a8-562c79e0ee4f/analysis 404 (Not Found)



#
勤怠管理
各項目をダブルクリックで編集

目標登録で不具合、ウェイト100なのに、ウェイト合計が100%超えているとメッセージされる。

電子稟議の新規起案で、領収書のようなファイル添付可能。


ストレスチェックの集団分析で404になる。

プロジェクト画面を追加。
「プロジェクト管理」画面の追加
プロジェクトの進行度をガントチャートで表示。
作業項目の追加編集可能。
プロジェクトの作業項目はチケット単位。
プロジェクトの作業項目、工程表のテンプレートダウンロード可能で、アップロードで一括登録。

ダッシュボードに自分のプロジェクトのガントチャートを表示


出退勤管理
勤怠一覧にて、出勤の横に出勤打刻時刻、退勤の横に退勤打刻時刻を表示（編集可能）
退勤の打刻はいつでも打刻可能。
24時でリセット。1日に1回まで出勤打刻可能。出勤打刻されると、退勤打刻をいつでも可能。


社員登録に顧客登録可能
社員登録にメールアドレス、電話番号は必須。

資格登録
社外の資格登録には、PDFまたはJPG、PNGなどの添付可能。

#
出退勤管理について

出勤時刻と出勤打刻時刻は別。退勤時刻と退勤打刻時刻は別。
出退勤管理では、4つとも並べて表示し、同様にダブルクリックで編集可能。
出勤打刻は出社時刻を意味し、
出勤時刻は勤務開始時刻、退勤打刻は出社時刻、退勤時刻は勤務終了時刻を意味する。
#
打刻時刻は秒単位、出社退勤は分単位で表示、
プロジェクト欄の横幅を2倍ほど少し広げる
打刻済みの扱いなのに、打刻時刻が表示されないバグ。
CSVの一括アップロード、ダウンロードで打刻時間は不要。
勤務開始、勤務終了を始業、就業に修正。


日報作成画面で、AIアシスタント利用可能。
イントラ記事作成も、AIアシスタント利用可能。

電子稟議の新規起案時にファイル添付可能。（見積書など）

チャット入力中にも、AIアシスタントの利用可能。


資格登録で、画像やpdfなどの添付が可能。（資格証明書や領収書）

プロジェクト管理画面では、
プロジェクト一括登録可能。
1列目：件番、2列目：プロジェクト名、3列目：管理者
管理者は複数名指定可能。主管理者と従管理者を指定可能。
プロジェクト一覧で、ダブルクリックで編集可能。
開始期間および終了期間は不明、未定が入力可能。
プロジェクト内の作業をチケット単位で追加可能。
作業チケットで



社員情報の追加で、ロールに顧客など全てのロールを選択可能

#
出勤打刻は一日一回押せる。
その後は退勤打刻を何度でも押せる。24時にリセットされる。

資格取得日の編集可能。
認定証を添付と同様に領収書添付

電子稟議の承認ボタンが反応しない。承認・却下には理由必須。

左のサイドバーを以下でカテゴライズ。
社員の機能、基本機能
上司の機能、承認機能など
管理部門（労務部）の機能
管理部門（人事部）の機能
管理部門（管理職）の機能
管理部門（経理職）の機能
システム管理機能

ダッシュボードにカレンダー表示。
カレンダーの休日はjpholidayから取得。
microsoft,googleカレンダーの同期可能。


月報作成で自己評価をつける。
月報で提出済みの年月は選択不可。

プロジェクト管理の主管理者は1人以上選択可能。


ストレスチェックの作成は労務部機能。
ストレスチェックの回答は社員の機能。
ストレスチェックのデフォルト項目はtemplate/stress_check_template.mdに格納。
ストレスチェックの作成はCSVでアップロード可能。



#
労務支援
ハラスメント研修
セキュリティ教育
受講履歴管理
その他法令順守の確認ため、集計

template/company_rule.mdは就業規則。この就業規則に、1ページに表示、2ページ目に改定版数と改定日、
ページ番号付与してpdfを作成




以下の機能を実装して。
ダッシュボードカレンダー + jpholiday + MS/Google同期（OAuth連携が必要）
月報の自己評価フィールド追加（DBマイグレーション必要）
プロジェクト主管理者の完全M2M化（再マイグレーション必要）


健康診断の受診
年1回義務





社員情報の、社員追加画面で以下のエラー
[HMR] connected
forward-logs-shared.ts:95 [Fast Refresh] rebuilding
:8000/api/v1/auth/me/:1  Failed to load resource: the server responded with a status of 401 (Unauthorized)Understand this error
:8000/api/v1/recruitment/jobs/:1  Failed to load resource: the server responded with a status of 401 (Unauthorized)Understand this error
forward-logs-shared.ts:95 [Fast Refresh] done in 7145ms
forward-logs-shared.ts:95 [Fast Refresh] rebuilding
forward-logs-shared.ts:95 [Fast Refresh] done in 2234ms
forward-logs-shared.ts:95 [Fast Refresh] rebuilding
forward-logs-shared.ts:95 [Fast Refresh] done in 1249ms
Unable to add filesystem: <illegal path>Understand this error


# ✅ 2026-04-24 コンプライアンスチェックリスト機能（フル実装）

## 概要
template/attention.md の労働管理チェックリスト（12セクション52項目）をDB管理し、ダッシュボードで進捗追跡可能に。

## バックエンド実装

### 新規アプリ: `apps/compliance/`

**models.py**
- `ComplianceChecklistSection`: 12セクション（健康診断、労働時間管理 など）
- `ComplianceChecklistItem`: 52個の具体的チェックリスト項目
- `ComplianceChecklistProgress`: ユーザーごとの完了状況（user + item で unique）
- 全て SoftDeleteModel 継承

**views.py - ComplianceChecklistViewSet**
```
GET    /api/v1/compliance/checklists/                  → セクション一覧 + 進捗率
GET    /api/v1/compliance/checklists/{id}/             → セクション詳細 + 全項目
GET    /api/v1/compliance/checklists/summary/          → 全体進捗サマリー
POST   /api/v1/compliance/checklists/update_item_progress/
       body: {item_id, is_completed, notes?}          → 項目完了状況更新
```

**serializers.py**
- `ComplianceChecklistSectionListSerializer`: 一覧用（進捗率集計）
- `ComplianceChecklistSectionDetailSerializer`: 詳細用（全項目含む）
- `ComplianceChecklistProgressSerializer`: 項目進捗

**migrations/**
- `0001_initial.py`: テーブル作成（デフォルトで削除済み除外）
- `0002_populate_checklist.py`: RunPython でデータ自動生成

**設定**
- settings.py: `'apps.compliance'` を INSTALLED_APPS に追加
- urls.py: `/api/v1/compliance/` ルート追加

### マイグレーション実行状況
✅ PowerShell で実行完了
```
cd C:\Users\MiyauchiHitoshi\HRM\backend && .\manage.py migrate compliance
```

## フロントエンド実装

### ダッシュボードウィジェット
**`frontend/src/app/(main)/components/ComplianceChecklist.tsx`**

**UI構造**
```
┌─ コンプライアンスチェックリスト
│  ├─ 全体進捗: 75% [プログレスバー色分け: 緑≥70% / 黄40-70% / 赤<40%]
│  ├─ 完了: 39/52 項目
│  └─ セクション一覧
│     ├─ 健康診断: 62% (5/8) [展開可能]
│     │  └─ ☑ 年1回の定期健康診断を実施している
│     │  └─ ☐ 対象者（週30時間以上等）を正しく抽出している
│     │  └─ ... (全8項目)
│     ├─ 労働時間管理: 83% (5/6)
│     └─ ... (全12セクション)
└─ ⚠️ 未完了25% - 定期的に確認してください
```

**機能**
- セクション展開時に REST API で詳細項目を非同期取得
- チェックボックスで項目完了/未完了を切り替え → 即座に進捗率再計算
- 重要項目（リスクチェック セクション全4項目）に赤ラベル表示
- 完了日時を自動記録

**実装詳細**
```typescript
// 全体進捗取得
useQuery({
  queryKey: ['compliance-summary'],
  queryFn: () => api.get('/api/v1/compliance/checklists/summary/'),
})

// セクション展開時に詳細取得
const toggleSection = async (sectionId: string) => {
  if (!sectionDetails[sectionId]) {
    const response = await api.get(`/api/v1/compliance/checklists/${sectionId}/`)
    setSectionDetails(prev => ({...prev, [sectionId]: response.data}))
  }
}

// 項目完了状況を更新
const updateItemMutation = useMutation({
  mutationFn: (payload) => 
    api.post('/api/v1/compliance/checklists/update_item_progress/', payload),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ['compliance-summary'] })
    qc.invalidateQueries({ queryKey: ['compliance-checklists'] })
  },
})
```

**ダッシュボード統合**
- `page.tsx` に `<ComplianceChecklist />` import & 配置
- カレンダーとプロジェクトタスク間に表示（顧客には非表示）

## データベーススキーマ

```sql
-- セクション（12個固定）
CREATE TABLE compliance_checklistsection (
  id UUID PRIMARY KEY,
  title VARCHAR(100),
  order SMALLINT,
  is_deleted BOOLEAN DEFAULT FALSE,
  ...timestamps...
);

-- 項目（52個）
CREATE TABLE compliance_checklistitem (
  id UUID PRIMARY KEY,
  section_id UUID REFERENCES compliance_checklistsection,
  title VARCHAR(200),
  order SMALLINT,
  is_critical BOOLEAN DEFAULT FALSE,    -- リスクチェック4項目のみTRUE
  is_deleted BOOLEAN DEFAULT FALSE,
  ...timestamps...
);

-- ユーザーごと進捗追跡
CREATE TABLE compliance_checklistprogress (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth_user,
  item_id UUID REFERENCES compliance_checklistitem,
  is_completed BOOLEAN DEFAULT FALSE,
  completed_at DATETIME NULL,          -- 完了日時
  notes TEXT,                          -- 備考
  is_deleted BOOLEAN DEFAULT FALSE,
  UNIQUE(user_id, item_id),            -- ユーザー+項目は一意
  ...timestamps...
);
```

## テストシナリオ

1. **初期表示**
   - ダッシュボードにウィジェット表示 ✓
   - 全体進捗 0% (未完了 0/52)

2. **セクション展開**
   - セクション展開 → API 呼び出し → 項目リスト表示 ✓
   - 重要項目に赤ラベル ✓

3. **項目完了**
   - チェックボックス ON → POST /update_item_progress/ → 進捗率更新
   - completed_at に現在時刻が記録される
   - 関連セクションの進捗率 + 全体進捗率がリアルタイム更新

4. **警告表示**
   - 進捗率 < 80% → ⚠️ メッセージ表示

## 拡張案（将来）

1. **セクション別期限管理**: セクションに期限を付与 → カレンダー連携
2. **部門別集計**: 部門/チーム単位の進捗ダッシュボード
3. **PDF エクスポート**: 進捗状況をレポートとして出力
4. **定期通知**: 月1回リマインダー通知
5. **監査ログ**: 誰がいつ何を完了したかを詳細記録

---

# ✅ 2026-04-29 カレンダー機能の完成

## 実装完了した機能

### 1. 祝日表示（holidays ライブラリ）
- `jpholiday` → `holidays` に変更
- API: `GET /api/v1/calendar/holidays/?year=YYYY&month=MM`
- 日本の祝日を赤色で表示

### 2. カレンダーの日付色分け
- **土曜日**: 青色背景 + 青色テキスト
- **日曜日**: 赤色背景 + 赤色テキスト
- 祝日: 赤色イベント表示

### 3. 日付ダブルクリック → 予定追加
- `dayCellDidMount` でクリックハンドラー追加
- 300ms以内の2回クリックでダブルクリック判定
- 予定追加モーダル表示
- バックエンド: `POST /api/v1/calendar/events/create/`

### 4. 予定クリック → 編集・削除
- 予定をクリックで編集モーダル表示
- タイトル・開始時刻・終了時刻を編集可能
- 削除ボタン（確認ダイアログ付き）
- バックエンド: 
  - `POST /api/v1/calendar/events/update_event/`
  - `POST /api/v1/calendar/events/delete_event/`

### 5. Microsoft/Google カレンダー同期
- OAuth スコープ: `Calendars.ReadWrite` / `calendar`
- トークン管理: `UserCalendarToken` モデル
- イベント自動同期

## API エンドポイント一覧

```
GET   /api/v1/calendar/holidays/               → 祝日一覧
GET   /api/v1/calendar/events/                 → カレンダーイベント
GET   /api/v1/calendar/oauth/ms/start/         → Microsoft 認証開始
GET   /api/v1/calendar/oauth/ms/callback/      → Microsoft コールバック
GET   /api/v1/calendar/oauth/google/start/     → Google 認証開始
GET   /api/v1/calendar/oauth/google/callback/  → Google コールバック
GET   /api/v1/calendar/tokens/                 → 連携プロバイダー一覧
POST  /api/v1/calendar/events/create/          → 予定作成
POST  /api/v1/calendar/events/update_event/    → 予定更新
POST  /api/v1/calendar/events/delete_event/    → 予定削除
POST  /api/v1/calendar/oauth/revoke/           → 連携解除
```

## トラブルシューティング

**エラー**: ChunkLoadError
- 原因: Next.js ビルドキャッシュ破損
- 解決: 
  ```bash
  rm -r .next node_modules package-lock.json
  npm install
  npm run dev
  ```

**エラー**: Unknown option 'dateClick'
- 原因: dayGridPlugin が dateClick をサポートしていない
- 解決: `dayCellDidMount` でクリックハンドラーを直接追加


#
一人の社員が複数のロールに登録可能。







