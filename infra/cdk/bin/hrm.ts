#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { HrmStack } from '../lib/hrm-stack';

const app = new cdk.App();

// コンテキスト（cdk deploy --context env=prod --context alertEmail=admin@example.com）
const env         = app.node.tryGetContext('env')        ?? 'prod';
const alertEmail  = app.node.tryGetContext('alertEmail') ?? undefined;

new HrmStack(app, `HrmStack-${env}`, {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'ap-northeast-1', // 東京リージョン固定
  },
  appEnv: env,
  alertEmail,   // 例: admin@example.com → CloudWatch・Budgets のアラート通知先
});

app.synth();
