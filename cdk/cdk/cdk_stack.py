########################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
########################################################################
import json
import os
from typing import Any, Dict

from aws_cdk import Duration, Stack
from aws_cdk.aws_iam import AnyPrincipal, Effect, PolicyStatement
from aws_cdk.aws_kms import Key
from aws_cdk.aws_lambda import DockerImageCode, DockerImageFunction, Runtime, Tracing
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion
from aws_cdk.aws_secretsmanager import Secret, SecretStringGenerator
from aws_cdk.aws_sqs import Queue
from constructs import Construct


class CdkStack(Stack):  # type: ignore
    """Stack for the AWS Lambda Oracle connection example."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Dict[str, Any]) -> None:
        """CDK entry point.

        Args:
            scope (Construct): scope of the cdk stack
            construct_id (str): construct id of the stack
        """
        super().__init__(scope, construct_id, **kwargs)

        kms_key = Key(
            self,
            "PyOracleKMSKey",
            description="KMS key for Py Oracle Connection",
            enable_key_rotation=True,
            pending_window=Duration.days(7),
        )

        secret = self.build_connection_secret(kms_key)
        self.build_lambda(kms_key, secret)

    def build_lambda(self, kms_key: Key, secret: Secret) -> None:
        """Build Lambda function with connection to Oracle database.

        Args:
            kms_key (Key): encryption key for the secret and env variables
            secret (Secret): secret used to store Oracle connection details

        Returns:
            DockerImageFunction: lambda function
        """
        stack_path = os.path.dirname(os.path.realpath(__file__))
        lambda_path = os.path.join(stack_path, "..", "..", "functions")
        thick_path = os.path.join(lambda_path, "thick")
        thin_path = os.path.join(lambda_path, "thin")
        thin_path_layer = os.path.join(lambda_path, "thin-layer")

        dlq = Queue(
            self,
            "PyOracleConnectionLambdaDLQ",
            encryption_master_key=kms_key,
            retention_period=Duration.days(5),
        )

        dlq.add_to_resource_policy(
            PolicyStatement(
                actions=["sqs:*"],
                effect=Effect.DENY,
                principals=[AnyPrincipal()],
                resources=[dlq.queue_arn],
                conditions={
                    "Bool": {"aws:secureTransport": "false"},
                },
            ),
        )

        fn_thick = DockerImageFunction(
            self,
            "PyOracleConnectionLambdaThick",
            function_name="py-oracle-connection-example-thick",
            code=DockerImageCode.from_image_asset(directory=thick_path),
            description="Example Lambda to illustrate connection to Oracle using Python (thick client)",
            dead_letter_queue=dlq,
            environment={
                "POWERTOOLS_SERVICE_NAME": "connection-example",
                "POWERTOOLS_METRICS_NAMESPACE": "PyOracleConn",
                "REGION": self.region,
                "SECRET_NAME": secret.secret_name,
            },
            environment_encryption=kms_key,
            memory_size=128,
            tracing=Tracing.ACTIVE,
            reserved_concurrent_executions=5,
            timeout=Duration.seconds(45),
        )

        fn_thin_layer = PythonLayerVersion(
            self,
            "PyOracleConnectionLambdaThinLayer",
            entry=thin_path_layer,
            compatible_runtimes=[Runtime.PYTHON_3_9],
        )

        fn_thin = PythonFunction(
            self,
            "PyOracleConnectionLambdaThin",
            function_name="py-oracle-connection-example-thin",
            description="Example Lambda to illustrate connection to Oracle using Python (thin client)",
            entry=thin_path,
            runtime=Runtime.PYTHON_3_9,
            index="lambda_handler.py",
            handler="handler",
            dead_letter_queue=dlq,
            layers=[fn_thin_layer],
            environment={
                "POWERTOOLS_SERVICE_NAME": "connection-example",
                "POWERTOOLS_METRICS_NAMESPACE": "PyOracleConn",
                "REGION": self.region,
                "SECRET_NAME": secret.secret_name,
            },
            environment_encryption=kms_key,
            memory_size=128,
            tracing=Tracing.ACTIVE,
            reserved_concurrent_executions=5,
            timeout=Duration.seconds(45),
        )

        for fn in [fn_thin, fn_thick]:
            kms_key.grant_decrypt(fn)
            secret.grant_read(fn)

    def build_connection_secret(self, kms_key: Key) -> Secret:
        """Secret for the Oracle DB Connection.

        Args:
            kms_key (Key): kms key for encryption

        Returns:
            Secret: secret in secret manager
        """
        template = SecretStringGenerator(
            secret_string_template=json.dumps({"host": "", "port": "", "sid": "", "username": ""}),
            generate_string_key="password",
        )

        return Secret(
            self,
            "PyOracleConnectionCredentials",
            generate_secret_string=template,
            encryption_key=kms_key,
            secret_name="py-oracle-connection-credentials",
        )
