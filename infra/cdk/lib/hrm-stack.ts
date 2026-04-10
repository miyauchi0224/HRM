import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as apprunner from 'aws-cdk-lib/aws-apprunner';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatchActions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as budgets from 'aws-cdk-lib/aws-budgets';
import { Construct } from 'constructs';

interface HrmStackProps extends cdk.StackProps {
  appEnv: string; // 'prod' のみ想定（7名規模・コスト最適化済み）
  alertEmail?: string; // アラート通知先メールアドレス
}

export class HrmStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: HrmStackProps) {
    super(scope, id, props);

    const { appEnv, alertEmail } = props;
    const prefix = `hrm-${appEnv}`;

    // =========================================================================
    // コスト最適化方針（7名規模）
    // ─ NAT Gateway（¥7,000/月）を廃止 → VPC Endpoint に置き換え
    // ─ RDS: t4g.micro / シングルAZ / 20GB
    // ─ App Runner: 0.25vCPU / 0.5GB（7名の同時アクセスは問題なし）
    // ─ バックアップ保持: 3日（7日→短縮）
    // ─ CloudWatch ログ保持: 1ヶ月
    // =========================================================================

    // =========================================================================
    // 1. VPC（NAT Gateway なし）
    //    プライベートサブネットからのインターネット通信は VPC Endpoint で代替。
    //    NATなしにすることで約¥7,000/月の削減。
    // =========================================================================
    const vpc = new ec2.Vpc(this, 'Vpc', {
      vpcName: `${prefix}-vpc`,
      maxAzs: 2,
      natGateways: 0, // ← NAT Gateway ゼロ！ここがコスト削減の核心
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          // Isolated = インターネットへの出口なし（DBなど内部専用）
          name: 'Isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
    });

    // =========================================================================
    // 2. VPC Endpoints
    //    「AWSのサービスへの通信をAWS内部ネットワークで完結させる」仕組み。
    //    NAT Gateway を使わずに S3・Secrets Manager・Bedrock 等へアクセスできる。
    //    Interface型（¥500/月/サービス）と Gateway型（無料）の2種類がある。
    // =========================================================================

    // --- Gateway型（無料）---
    // S3へのアクセスはGateway型VPC Endpointで完全無料
    vpc.addGatewayEndpoint('S3Endpoint', {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });

    // --- Interface型（有料：¥500/月/サービス 程度）---
    // Secrets Manager（DBパスワード取得用）
    vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      privateDnsEnabled: true, // プライベートDNSを有効化（エンドポイントのURLを意識せず使える）
    });

    // CloudWatch Logs（アプリログ送信用）
    vpc.addInterfaceEndpoint('CloudWatchLogsEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      privateDnsEnabled: true,
    });

    // Bedrock（AI機能呼び出し用）
    vpc.addInterfaceEndpoint('BedrockEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      privateDnsEnabled: true,
    });

    // Cognito（JWT検証用）
    vpc.addInterfaceEndpoint('CognitoEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.COGNITO_IDP,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      privateDnsEnabled: true,
    });

    // =========================================================================
    // 3. Secrets Manager（DBパスワード管理）
    // =========================================================================
    const dbSecret = new secretsmanager.Secret(this, 'DbSecret', {
      secretName: `${prefix}/db-credentials`,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'hrm_admin' }),
        generateStringKey: 'password',
        excludeCharacters: '"@/\\',
        passwordLength: 32,
      },
    });

    // =========================================================================
    // 4. Amazon RDS for PostgreSQL（コスト最適化構成）
    //    t4g.micro: Graviton2（ARM）プロセッサ採用の最小インスタンス。
    //    t3.microより約20%安く、7名規模には十分な性能。
    //    シングルAZ: 冗長化なし。障害時は数分のダウンタイムあり（社内システムで許容）。
    // =========================================================================
    const dbSg = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc,
      securityGroupName: `${prefix}-db-sg`,
      description: 'RDS PostgreSQL security group',
    });

    const dbInstance = new rds.DatabaseInstance(this, 'Database', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16,
      }),
      // t4g.micro: Graviton2（ARM）の最小インスタンス。7名なら十分。
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [dbSg],
      credentials: rds.Credentials.fromSecret(dbSecret),
      databaseName: 'hrm',
      instanceIdentifier: `${prefix}-db`,
      backupRetention: cdk.Duration.days(3), // 7日→3日に短縮（ストレージ削減）
      deletionProtection: true,
      multiAz: false,           // シングルAZ（コスト半減）
      storageEncrypted: true,
      allocatedStorage: 20,      // 20GB（7名なら十分）
      maxAllocatedStorage: 50,   // 自動拡張上限50GB
      storageType: rds.StorageType.GP3, // gp3: gp2より安くI/Oも速い
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // =========================================================================
    // 5. Amazon S3 バケット
    // =========================================================================
    const storageBucket = new s3.Bucket(this, 'StorageBucket', {
      bucketName: `${prefix}-storage-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: false, // 7名規模ではバージョニング不要（ストレージ節約）
      lifecycleRules: [
        {
          id: 'delete-temp-files',
          prefix: 'temp/',
          expiration: cdk.Duration.days(1),
        },
        {
          // 古いPDF・XLSXを180日でGlacier移行（ストレージコスト削減）
          id: 'archive-old-files',
          prefix: 'payslips/',
          transitions: [{
            storageClass: s3.StorageClass.GLACIER,
            transitionAfter: cdk.Duration.days(180),
          }],
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          maxAge: 3000,
        },
      ],
    });

    const templateBucket = new s3.Bucket(this, 'TemplateBucket', {
      bucketName: `${prefix}-templates-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // =========================================================================
    // 6. AWS Cognito（7名まで完全無料 ← 無料枠: 5万MAU/月）
    // =========================================================================
    const userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: `${prefix}-user-pool`,
      signInAliases: { email: true },
      signInCaseSensitive: false,
      passwordPolicy: {
        minLength: 12,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
        tempPasswordValidity: cdk.Duration.days(7),
      },
      mfa: cognito.Mfa.OPTIONAL,
      mfaSecondFactor: { sms: false, otp: true },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      selfSignUpEnabled: false,
      autoVerify: { email: true },
      standardAttributes: {
        email: { required: true, mutable: true },
        givenName: { required: true, mutable: true },
        familyName: { required: true, mutable: true },
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const userPoolClient = userPool.addClient('WebClient', {
      userPoolClientName: `${prefix}-web-client`,
      authFlows: { userPassword: true, userSrp: true },
      accessTokenValidity: cdk.Duration.hours(1),
      refreshTokenValidity: cdk.Duration.days(30),
      preventUserExistenceErrors: true,
    });

    // =========================================================================
    // 7. IAM ロール（App Runner 用）
    // =========================================================================
    const appRunnerRole = new iam.Role(this, 'AppRunnerRole', {
      roleName: `${prefix}-apprunner-role`,
      assumedBy: new iam.ServicePrincipal('tasks.apprunner.amazonaws.com'),
    });

    storageBucket.grantReadWrite(appRunnerRole);
    templateBucket.grantRead(appRunnerRole);
    dbSecret.grantRead(appRunnerRole);

    appRunnerRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: [`arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-sonnet-4-5*`],
    }));

    appRunnerRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'cognito-idp:AdminCreateUser',
        'cognito-idp:AdminDeleteUser',
        'cognito-idp:AdminDisableUser',
        'cognito-idp:AdminEnableUser',
        'cognito-idp:AdminSetUserPassword',
        'cognito-idp:AdminGetUser',
        'cognito-idp:ListUsers',
      ],
      resources: [userPool.userPoolArn],
    }));

    // ECR アクセスロール
    new iam.Role(this, 'AppRunnerAccessRole', {
      roleName: `${prefix}-apprunner-access-role`,
      assumedBy: new iam.ServicePrincipal('build.apprunner.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AWSAppRunnerServicePolicyForECRAccess'
        ),
      ],
    });

    // =========================================================================
    // 8. CloudWatch ロググループ（保持期間1ヶ月に短縮）
    // =========================================================================
    const appLogGroup = new logs.LogGroup(this, 'AppLogGroup', {
      logGroupName: `/hrm/${appEnv}/app-runner`,
      retention: logs.RetentionDays.ONE_MONTH, // 3ヶ月→1ヶ月（ログ保管コスト削減）
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // =========================================================================
    // 9. SNS トピック（アラート通知）
    // =========================================================================
    const alertTopic = new sns.Topic(this, 'AlertTopic', {
      topicName: `${prefix}-alerts`,
      displayName: `HRM Alerts`,
    });

    // メールアドレスが設定されていれば通知先として登録
    if (alertEmail) {
      alertTopic.addSubscription(
        new (require('aws-cdk-lib/aws-sns-subscriptions').EmailSubscription)(alertEmail)
      );
    }

    // =========================================================================
    // 10. CloudWatch アラーム
    // =========================================================================
    new cloudwatch.Alarm(this, 'RdsCpuAlarm', {
      alarmName: `${prefix}-rds-cpu-high`,
      alarmDescription: 'RDS CPU 80%超',
      metric: dbInstance.metricCPUUtilization(),
      threshold: 80,
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    }).addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));

    new cloudwatch.Alarm(this, 'RdsDiskAlarm', {
      alarmName: `${prefix}-rds-disk-low`,
      alarmDescription: 'RDS 空きストレージ 2GB未満',
      metric: dbInstance.metricFreeStorageSpace(),
      threshold: 2 * 1024 * 1024 * 1024, // 2GB
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
    }).addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));

    // =========================================================================
    // 11. AWS Budgets（月額コストアラート）
    //     月$80（約¥12,000）を超えたらメール通知。過剰課金を早期検知。
    // =========================================================================
    new budgets.CfnBudget(this, 'MonthlyBudget', {
      budget: {
        budgetName: `${prefix}-monthly-budget`,
        budgetType: 'COST',
        timeUnit: 'MONTHLY',
        budgetLimit: {
          amount: 80,   // USD
          unit: 'USD',
        },
      },
      notificationsWithSubscribers: alertEmail ? [
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 80,   // 80%（$64）で事前通知
            thresholdType: 'PERCENTAGE',
          },
          subscribers: [{ subscriptionType: 'EMAIL', address: alertEmail }],
        },
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 100,  // 100%（$80）で超過通知
            thresholdType: 'PERCENTAGE',
          },
          subscribers: [{ subscriptionType: 'EMAIL', address: alertEmail }],
        },
      ] : [],
    });

    // =========================================================================
    // 12. App Runner（Djangoバックエンド・最小構成）
    //     0.25vCPU / 0.5GB: 7名の同時アクセスには十分な性能。
    //     アイドル時もリクエスト待機インスタンスが1台起動し続けることに注意。
    // =========================================================================
    const appRunnerService = new apprunner.CfnService(this, 'AppRunnerService', {
      serviceName: `${prefix}-backend`,
      sourceConfiguration: {
        autoDeploymentsEnabled: false,
        imageRepository: {
          imageIdentifier: 'public.ecr.aws/docker/library/python:3.12-slim',
          imageRepositoryType: 'ECR_PUBLIC',
          imageConfiguration: {
            port: '8000',
            runtimeEnvironmentVariables: [
              { name: 'DJANGO_ENV',             value: appEnv },
              { name: 'DJANGO_ALLOWED_HOSTS',   value: '*' },
              { name: 'AWS_REGION',             value: 'ap-northeast-1' },
              { name: 'COGNITO_USER_POOL_ID',   value: userPool.userPoolId },
              { name: 'COGNITO_APP_CLIENT_ID',  value: userPoolClient.userPoolClientId },
              { name: 'S3_STORAGE_BUCKET',      value: storageBucket.bucketName },
              { name: 'S3_TEMPLATE_BUCKET',     value: templateBucket.bucketName },
              { name: 'DB_SECRET_ARN',          value: dbSecret.secretArn },
              { name: 'DB_HOST',                value: dbInstance.instanceEndpoint.hostname },
              { name: 'DB_PORT',                value: '5432' },
              { name: 'DB_NAME',                value: 'hrm' },
            ],
          },
        },
      },
      instanceConfiguration: {
        cpu: '0.25 vCPU', // 最小スペック（7名に十分）
        memory: '0.5 GB',
        instanceRoleArn: appRunnerRole.roleArn,
      },
      healthCheckConfiguration: {
        protocol: 'HTTP',
        path: '/api/v1/health/',
        interval: 20,          // チェック間隔を長めに（コスト微削減）
        timeout: 5,
        healthyThreshold: 1,
        unhealthyThreshold: 3,
      },
      observabilityConfiguration: {
        observabilityEnabled: true,
      },
    });

    // RDSセキュリティグループにVPCからの5432ポートアクセスを許可
    dbSg.addIngressRule(
      ec2.Peer.ipv4(vpc.vpcCidrBlock),
      ec2.Port.tcp(5432),
      'Allow PostgreSQL from VPC'
    );

    // =========================================================================
    // 13. Outputs（デプロイ後に表示される値 → backend/.env に設定）
    // =========================================================================
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
      description: '→ COGNITO_USER_POOL_ID',
      exportName: `${prefix}-user-pool-id`,
    });
    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: userPoolClient.userPoolClientId,
      description: '→ COGNITO_APP_CLIENT_ID',
      exportName: `${prefix}-user-pool-client-id`,
    });
    new cdk.CfnOutput(this, 'StorageBucketName', {
      value: storageBucket.bucketName,
      description: '→ S3_STORAGE_BUCKET',
      exportName: `${prefix}-storage-bucket`,
    });
    new cdk.CfnOutput(this, 'TemplateBucketName', {
      value: templateBucket.bucketName,
      description: '→ S3_TEMPLATE_BUCKET',
      exportName: `${prefix}-template-bucket`,
    });
    new cdk.CfnOutput(this, 'DbEndpoint', {
      value: dbInstance.instanceEndpoint.hostname,
      description: '→ DB_HOST',
      exportName: `${prefix}-db-endpoint`,
    });
    new cdk.CfnOutput(this, 'DbSecretArn', {
      value: dbSecret.secretArn,
      description: '→ DB_SECRET_ARN',
      exportName: `${prefix}-db-secret-arn`,
    });
    new cdk.CfnOutput(this, 'AppRunnerServiceUrl', {
      value: cdk.Fn.getAtt(appRunnerService.logicalId, 'ServiceUrl').toString(),
      description: 'バックエンドAPI URL',
      exportName: `${prefix}-api-url`,
    });
    new cdk.CfnOutput(this, 'AppLogGroupName', {
      value: appLogGroup.logGroupName,
      description: 'CloudWatch ロググループ名',
    });
    new cdk.CfnOutput(this, 'EstimatedMonthlyCost', {
      value: '~$59 USD / ~8,850 JPY（7名規模・最適化済み）',
      description: '月額コスト概算',
    });

    // タグ付与（コスト管理・検索に便利）
    cdk.Tags.of(this).add('Project', 'HRM');
    cdk.Tags.of(this).add('Environment', appEnv);
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
  }
}
