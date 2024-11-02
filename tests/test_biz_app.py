from unittest.mock import patch

import pytest

from appsvc.biz.app import get_preferred_dcs
from appsvc.biz.models import UsersDcsDAO

TEST_USER_ID = 0
TEST_DATA_CENTERS = ["us-west-1", "us-east-1", "eu-central-1"]


@pytest.mark.unit
class TestBizApp:
    @patch("appsvc.biz.app.sqldb.session.query")
    def test_get_preferred_dcs(self, mock_query):
        # unknown user
        mock_query.return_value.filter.return_value.first.return_value = None
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == TEST_DATA_CENTERS

        # user with 1 known DC
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [1.0]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["us-east-1", "eu-central-1", "us-west-1"]

        # user from West US with 2 known DCs
        # TODO: make it smart and don't go further to the East if West is already the best)
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [1.0], "us-east-1": [2.0]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["eu-central-1", "us-west-1", "us-east-1"]

        # user from EU with 2 known DCs
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [2.0], "us-east-1": [1.0]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["eu-central-1", "us-east-1", "us-west-1"]

        # user with 3 known DCs
        mock_query.return_value.filter.return_value.first.return_value = UsersDcsDAO(
            user_id=TEST_USER_ID, dcs={"us-west-1": [2.0], "us-east-1": [1.0], "eu-central-1": [1.5]}
        )
        assert get_preferred_dcs(TEST_USER_ID, TEST_DATA_CENTERS) == ["us-east-1", "eu-central-1", "us-west-1"]
