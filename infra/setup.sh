#!/usr/bin/env bash
# =============================================================================
# HRM - AWS環境セットアップスクリプト
# 実行前に以下をインストールしておいてください：
#   - AWS CLI v2  : https://aws.amazon.com/cli/
#   - Node.js 20+ : https://nodejs.org/
#   - Docker      : https://www.docker.com/
# =============================================================================
set -e

# --- 色付きログ出力 -----------------------------------------------------------
info()    { echo -e "\033[1;34m[INFO]\033[0m $*"; }
success() { echo -e "\033[1;32m[OK]\033[0m $*"; }
error()   { echo -e "\033[1;31m[ERROR]\033[0m $*"; exit 1; }

# --- 設定値（必要に応じて変更してください） -----------------------------------
AWS_REGION="ap-northeast-1"        # 東京リージョン
AWS_PROFILE="${AWS_PROFILE:-default}"
APP_NAME="hrm"
ENV="${ENV:-dev}"                   # dev / stg / prod

# =============================================================================
# 1. 前提条件チェック
# =============================================================================
info "前提条件を確認しています..."

command -v aws    >/dev/null 2>&1 || error "AWS CLI がインストールされていません。https://aws.amazon.com/cli/ からインストールしてください"
command -v node   >/dev/null 2>&1 || error "Node.js がインストールされていません。https://nodejs.org/ からインストールしてください"
command -v npm    >/dev/null 2>&1 || error "npm がインストールされていません"
command -v docker >/dev/null 2>&1 || error "Docker がインストールされていません"

AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1)
NODE_VERSION=$(node --version)
success "AWS CLI: $AWS_VERSION"
success "Node.js: $NODE_VERSION"

# =============================================================================
# 2. AWS 認証確認
# =============================================================================
info "AWS 認証を確認しています（プロファイル: $AWS_PROFILE）..."

AWS_ACCOUNT_ID=$(aws sts get-caller-identity \
  --profile "$AWS_PROFILE" \
  --query "Account" \
  --output text 2>/dev/null) \
  || error "AWS 認証に失敗しました。'aws configure' または 'aws sso login' で認証してください"

success "AWSアカウントID: $AWS_ACCOUNT_ID（リージョン: $AWS_REGION）"

# =============================================================================
# 3. AWS CDK インストール＆Bootstrap
# =============================================================================
info "AWS CDK をセットアップしています..."

# CDK CLI がなければグローバルインストール
if ! command -v cdk >/dev/null 2>&1; then
  info "AWS CDK CLI をインストールしています..."
  npm install -g aws-cdk
fi
success "CDK バージョン: $(cdk --version)"

# CDK 依存パッケージインストール
info "CDK プロジェクトの依存パッケージをインストールしています..."
cd "$(dirname "$0")/cdk"
npm install
cd -

# CDK Bootstrap（初回のみ必要。AWSアカウントにCDK用S3バケット等を作成する）
info "CDK Bootstrap を実行しています（初回のみ時間がかかります）..."
cdk bootstrap \
  "aws://$AWS_ACCOUNT_ID/$AWS_REGION" \
  --profile "$AWS_PROFILE" \
  --toolkit-stack-name "CDKToolkit-$APP_NAME"

success "CDK Bootstrap 完了"

# =============================================================================
# 4. S3バケット作成（テンプレートファイル用）
# =============================================================================
TEMPLATE_BUCKET="${APP_NAME}-${ENV}-templates-${AWS_ACCOUNT_ID}"

info "S3バケット（テンプレート用）を確認しています: $TEMPLATE_BUCKET"

if aws s3api head-bucket --bucket "$TEMPLATE_BUCKET" --profile "$AWS_PROFILE" 2>/dev/null; then
  success "S3バケットはすでに存在します: $TEMPLATE_BUCKET"
else
  info "S3バケットを作成しています..."
  aws s3api create-bucket \
    --bucket "$TEMPLATE_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION" \
    --profile "$AWS_PROFILE"

  # パブリックアクセスをすべてブロック（セキュリティ設定）
  aws s3api put-public-access-block \
    --bucket "$TEMPLATE_BUCKET" \
    --public-access-block-configuration \
      "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --profile "$AWS_PROFILE"

  success "S3バケット作成完了: $TEMPLATE_BUCKET"
fi

# テンプレートファイルをアップロード
TEMPLATE_DIR="$(dirname "$0")/../template"
if [ -d "$TEMPLATE_DIR" ]; then
  info "テンプレートファイルをS3にアップロードしています..."
  aws s3 sync "$TEMPLATE_DIR" "s3://$TEMPLATE_BUCKET/templates/" \
    --profile "$AWS_PROFILE"
  success "テンプレートファイルのアップロード完了"
fi

# =============================================================================
# 5. CDK デプロイ
# =============================================================================
info "CDK スタックをデプロイしています（環境: $ENV）..."
cd "$(dirname "$0")/cdk"

cdk deploy "*" \
  --profile "$AWS_PROFILE" \
  --context env="$ENV" \
  --context accountId="$AWS_ACCOUNT_ID" \
  --require-approval never

cd -
success "デプロイ完了！"

# =============================================================================
# 完了メッセージ
# =============================================================================
echo ""
echo "=============================================="
echo "  HRM AWS環境のセットアップが完了しました"
echo "  アカウント : $AWS_ACCOUNT_ID"
echo "  リージョン : $AWS_REGION"
echo "  環境       : $ENV"
echo "=============================================="
echo ""
info "次のステップ："
echo "  1. .env.example をコピーして backend/.env を作成"
echo "  2. CDK出力のエンドポイント等を .env に設定"
echo "  3. docker-compose up でローカル開発環境を起動"
