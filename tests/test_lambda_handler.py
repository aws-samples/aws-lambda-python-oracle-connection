########################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
########################################################################

import importlib
from typing import Any
from unittest import mock
from unittest.mock import MagicMock

import pytest


class TestLambdaHandler:
    """Tests for the lambda handler."""

    TABLES = ["table1", "table2", "table3"]

    @pytest.fixture(params=["thick", "thin"])
    def lambda_handler(self, request: Any) -> Any:
        """Imports lambda handler for both thick and thin mode.

        Args:
            request (Any): _description_

        Returns:
            Any: _description_
        """
        return importlib.import_module(f"functions.{request.param}.lambda_handler")

    @pytest.fixture()
    def mock_connection(self) -> MagicMock:
        """
        Mock Oracle database connection.

        Returns:
            mock of database connection
        """
        connection_mock = MagicMock()
        connection_mock.cursor().__enter__().fetchall.return_value = self.TABLES
        return connection_mock

    def test_query_should_return_tables(self, mock_connection: MagicMock, lambda_handler: Any) -> None:
        """Test query should return tables.

        Args:
            mock_connection (MagicMock): connection mock to database
            lambda_handler (Any): module of lambda handler to test
        """
        lambda_handler.parameters = MagicMock()
        lambda_handler.cx_Oracle.connect().__enter__.return_value = mock_connection
        result = lambda_handler.handler(None, None)
        assert self.TABLES == result

    def test_query_should_fail_on_connection_issue(self, lambda_handler: Any) -> None:
        """Test query should fail when connection to database fails.

        Args:
            lambda_handler (Any): module of lambda handler to test
        """
        lambda_handler.parameters = MagicMock()
        lambda_handler.cx_Oracle.connect().__enter__.side_effect = ValueError()
        with pytest.raises(ValueError):
            lambda_handler.handler(None, None)
