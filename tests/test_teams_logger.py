import json
import unittest.mock
from logging import Handler, INFO, getLogger, LogRecord

from teams_logger import TeamsHandler, Office365CardFormatter


class TestOffice365CardFormatter(unittest.TestCase):
    log_record = LogRecord(name="logger", level=INFO, pathname=__name__, lineno=1, msg="hello %s",
                           args=("world",), exc_info=None)
    facts_parameter = ["name"]
    expected_facts_in_message_card = [{
        "name": "name",
        "value": "logger"
    }]
    expected_text_in_message_card = "hello world"

    @classmethod
    def setUpClass(cls) -> None:
        cls.expected_formatted_message_card = {
            "@context": "https://schema.org/extensions",
            "@type": "MessageCard",
            "sections": [{
                "facts": cls.expected_facts_in_message_card
            }],
            "text": cls.expected_text_in_message_card
        }
        cls.formatter = Office365CardFormatter(facts=cls.facts_parameter)

    def test_format(self):
        formatted_message_card = self.formatter.format(self.log_record)
        self.assert_cards_equal(self.expected_formatted_message_card, json.loads(formatted_message_card))

    def assert_cards_equal(self, expected_card, actual_card):
        """
        Reorder the facts before sorting the cards.
        """
        expected_facts: list = expected_card["sections"][0]["facts"]
        expected_facts.sort(key=lambda x: x["name"])
        actual_facts = actual_card["sections"][0]["facts"]
        actual_facts.sort(key=lambda x: x["name"])
        self.assertEqual(expected_card, actual_card)


class TestOffice365CardFormatter2(TestOffice365CardFormatter):
    facts_parameter = ["name", "levelname", "lineno"]
    expected_facts_in_message_card = [{
        "name": "name",
        "value": "logger"
    }, {
        "name": "lineno",
        "value": 1
    }, {
        "name": "levelname",
        "value": "INFO"
    }]


class TestTeamsHandler(unittest.TestCase):
    url = 'https://outlook.office.com/webhook/fake_id/IncomingWebhook/fake_id'
    level = INFO
    log_text = "bla bla %s"
    log_parameter = "foo"
    log_level = INFO
    fake_message_card = "fake message card"

    @classmethod
    def setUpClass(cls) -> None:
        log_message = cls.log_text % cls.log_parameter
        cls.expected_payload_with_default_formatter = json.dumps({
            "text": log_message
        })

    def setUp(self) -> None:
        self.teams_handler = TeamsHandler(url=self.url, level=self.level)
        self.teams_handler.formatter = None
        self.logger = getLogger(__name__)
        self.logger.setLevel(self.level)
        self.logger.handlers = [self.teams_handler]

    def test_is_handler(self):
        assert issubclass(TeamsHandler, Handler)

    def test_properties(self):
        handler = TeamsHandler(url=self.url, level=self.level)
        assert self.url == handler.url
        assert self.level == handler.level

    @unittest.mock.patch("requests.post")
    def test_emit_with_default_formatter(self, mock_requests):
        self.logger.log(self.log_level, self.log_text, self.log_parameter)
        mock_requests.assert_called_with(url=self.url, headers={"Content-Type": "application/json"},
                                         data=self.expected_payload_with_default_formatter)

    @unittest.mock.patch("requests.post")
    def test_emit_with_teams_message_card_formatter(self, mock_requests):
        teams_message_card_formatter = Office365CardFormatter(facts=[])
        teams_message_card_formatter.format = unittest.mock.MagicMock(return_value=self.fake_message_card)
        self.teams_handler.setFormatter(teams_message_card_formatter)
        self.logger.log(self.log_level, self.log_text, self.log_parameter)
        mock_requests.assert_called_with(url=self.url, headers={"Content-Type": "application/json"},
                                         data=self.fake_message_card)


if __name__ == '__main__':
    unittest.main()
