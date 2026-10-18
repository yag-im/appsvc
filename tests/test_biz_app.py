import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.dialects.postgresql import psycopg

from appsvc.biz.app import get_preferred_dcs
from appsvc.biz.models import (
    AppReleaseDAO,
    UsersDcsDAO,
)

TEST_USER_ID = 0
TEST_DATA_CENTERS = ["us-west-1", "us-east-1", "eu-central-1"]


@pytest.mark.unit
class TestBizApp:
    def test_release_uuidv4_loaded_as_str(self):
        # psycopg returns native uuid columns as uuid.UUID; DTOs expect str
        dialect = psycopg.dialect()
        col_type = AppReleaseDAO.__table__.c.uuidv4.type
        process = col_type.dialect_impl(dialect).result_processor(dialect, None)
        value = "f22fc39e-8190-4c0f-b462-fdc7daddbdb6"
        assert process(uuid.UUID(value)) == value
        assert process(None) is None

    @patch("appsvc.biz.app.sqldb.session.query")
    def test_get_preferred_dcs(self, mock_query):
        # new user
        mock_query.return_value.filter.return_value.first.return_value = None
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == TEST_DATA_CENTERS

        # user with 1 known DC
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [1.0, 1.3]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["us-east-1", "eu-central-1", "us-west-1"]

        # user with 1 known good DC
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [0.037, 0.045]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["us-west-1", "us-east-1", "eu-central-1"]

        # user with 1 known good DC
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [0.067, 0.087], "us-east-1": [0.037, 0.045]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["us-east-1", "eu-central-1", "us-west-1"]

        # user from West US with 2 known DCs
        # TODO: make it smart and don't go further to the East if West is already the best)
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [1.0, 1.1], "us-east-1": [2.0, 2.1]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["eu-central-1", "us-west-1", "us-east-1"]

        # user from EU with 2 known DCs
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [2.0, 2.1], "us-east-1": [1.0, 1.1]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["eu-central-1", "us-east-1", "us-west-1"]

        # user with 3 known DCs
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [2.0, 2.3], "us-east-1": [1.0, 0.4], "eu-central-1": [1.5, 1.6]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["us-east-1", "eu-central-1", "us-west-1"]
