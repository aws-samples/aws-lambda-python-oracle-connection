########################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
########################################################################

import os
from typing import Any, Dict, List

import oracledb as cx_Oracle
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


REGION = os.getenv("REGION")
SECRET_NAME = os.getenv("SECRET_NAME")

tracer = Tracer()
logger = Logger()
metrics = Metrics()
cx_Oracle.init_oracle_client()


@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event: Dict[str, Any], _: LambdaContext) -> List[str]:
    """
    Lambda function example to connect to Oracle database using python-oracledb.

    Keep in mind that this function will open a single connection on each execution
    and therefore measures need to be put in place to not overwhelm the database -
    either through a proxy or limiting the concurrency.

    Args:
        event: Lambda event - ignored for now
        context: lambda context
    """
    logger.info(f"fetching secret {SECRET_NAME} from secret manager")
    secret = parameters.get_secret(SECRET_NAME, transform="json")

    dsn = cx_Oracle.makedsn(secret["host"], secret["port"], secret["sid"])
    logger.info(f"connecting to oracle database: {dsn}")

    with cx_Oracle.connect(
        user=secret["username"],
        password=secret["password"],
        dsn=dsn,
        encoding="UTF-8",
    ) as connection:
        query = """
            SELECT
                table_name
            FROM
                all_tables
        """
        logger.info(f"displaying all accessible tables in database.")
        with connection.cursor() as cursor:
            cursor.execute(query)
            tables: List[str] = cursor.fetchall()
            logger.info(f"found {len(tables)} tables: {tables}")
            return tables
