########################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
########################################################################

from multiprocessing.sharedctypes import Value
from unittest import mock
from unittest.mock import MagicMock

import lambda_handler
import pytest


class TestLambdaHandler:
    """Tests for the lambda handler."""

    TABLES = ["table1", "table2", "table3"]

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

    def teardown_method(self) -> None:
        """Cleanup."""
        lambda_handler.cx_Oracle = MagicMock()  # type: ignore

    @mock.patch("lambda_handler.parameters", MagicMock())
    def test_query_should_return_tables(self, mock_connection: MagicMock) -> None:
        """Test query should return tables.

        Args:
            mock_connection (MagicMock): connection mock to database
        """
        lambda_handler.cx_Oracle.connect().__enter__.return_value = mock_connection  # type: ignore
        result = lambda_handler.handler(None, None)
        assert self.TABLES == result

    @mock.patch("lambda_handler.parameters", MagicMock())
    def test_query_should_fail_on_connection_issue(self) -> None:
        """Test query should fail when connection to database fails."""
        lambda_handler.cx_Oracle.connect().__enter__.side_effect = ValueError()  # type: ignore
        with pytest.raises(ValueError):
            lambda_handler.handler(None, None)
