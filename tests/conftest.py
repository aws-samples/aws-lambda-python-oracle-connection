########################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
########################################################################

import os
import sys
from unittest.mock import MagicMock


sys.modules["oracledb"] = MagicMock()
os.environ["REGION"] = "eu-central-1"
os.environ["SECRET_NAME"] = "mock-secret"
