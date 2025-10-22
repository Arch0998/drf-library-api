from unittest.mock import patch

from notifications.telegram_helper import send_telegram_message


def test_send_telegram_message_success():
    with patch("notifications.telegram_helper.requests.post") as mock_post:
        mock_post.return_value.ok = True
        assert send_telegram_message("test") is True
        mock_post.assert_called_once()


def test_send_telegram_message_fail():
    with patch("notifications.telegram_helper.requests.post") as mock_post:
        mock_post.return_value.ok = False
        assert send_telegram_message("test") is False
        mock_post.assert_called_once()
