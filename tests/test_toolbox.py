"""Offline regression checks: mock only HTTP, environment and CLI input."""

import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch

import requests

# Never load a developer's .env while collecting the test suite.
with patch("dotenv.load_dotenv"):
    from main import main
    from src.router import route_query
    from src.tools import get_exchange_rate


def response(payload, status=200):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(payload).encode("utf-8")
    result.url = "https://example.invalid/v6/AUDIT_TEST_KEY/latest/USD"
    return result


def successful_payload(rate=7.12):
    return {
        "result": "success",
        "base_code": "USD",
        "conversion_rates": {"USD": 1, "CNY": rate},
    }


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        network = patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Offline tests must not access the network"),
        )
        network.start()
        self.addCleanup(network.stop)


class RoutingTests(OfflineCase):
    def test_time_identifies_the_machine_local_time(self):
        self.assertIn("本机", route_query("现在几点"))

    def test_weather_labels_fixed_sample_without_answering_requested_place_or_day(self):
        result = route_query("上海明天天气")
        self.assertIn("演示", result)
        self.assertIn("未查询", result)
        self.assertIn("城市", result)
        self.assertIn("日期", result)
        self.assertNotIn("今天天气晴", result)

    def test_clear_usd_cny_requests_reach_real_rate_boundary(self):
        os.environ["EXCHANGE_API_KEY"] = "AUDIT_TEST_KEY"
        for query in ["美元兑人民币汇率", "USD/CNY", "  usd / cny  ", "请查询当前美元兑人民币汇率是多少？"]:
            with self.subTest(query=query), patch(
                "src.tools.requests.get", return_value=response(successful_payload())
            ) as http:
                result = route_query(query)
                self.assertIn("7.12", result)
                self.assertIn("USD", result)
                self.assertIn("CNY", result)
                http.assert_called_once()

    def test_generic_rate_request_requires_an_explicit_pair(self):
        result = route_query("查汇率")
        self.assertIn("明确", result)
        self.assertNotIn("7.20", result)

    def test_english_currency_codes_accept_chinese_connectors(self):
        os.environ["EXCHANGE_API_KEY"] = "AUDIT_TEST_KEY"
        for query in ["USD兑CNY", "USD对RMB", "USD到CNY", "usd到cny"]:
            with self.subTest(query=query), patch(
                "src.tools.requests.get", return_value=response(successful_payload())
            ):
                self.assertIn("1 USD = 7.12 CNY", route_query(query))

    def test_other_or_reversed_currencies_are_not_silently_converted_to_usd_cny(self):
        for query in ["欧元兑日元汇率", "EUR/JPY", "人民币兑美元汇率", "CNY/USD", "USD/EUR"]:
            with self.subTest(query=query):
                result = route_query(query)
                self.assertIn("仅支持", result)
                self.assertNotIn("7.20", result)

    def test_amount_conversion_is_not_answered_with_a_unit_rate(self):
        self.assertIn("不支持", route_query("100美元兑人民币是多少"))

    def test_currency_history_question_does_not_trigger_rate_lookup(self):
        result = route_query("人民币为什么叫人民币")
        self.assertIn("明确", result)
        self.assertNotIn("7.20", result)

    def test_multiple_tools_require_separate_questions(self):
        for query in ["今天天气和汇率", "时间和天气", "现在几点，美元兑人民币汇率呢"]:
            with self.subTest(query=query):
                self.assertIn("多个", route_query(query))

    def test_mixed_language_currency_requests_still_count_as_another_tool(self):
        for query in ["天气和USD兑CNY", "时间和USD到CNY", "天气和EUR兑JPY"]:
            with self.subTest(query=query):
                self.assertIn("多个", route_query(query))

    def test_unrecognized_query_has_actionable_help(self):
        result = route_query("你好")
        self.assertIn("时间", result)
        self.assertIn("天气", result)
        self.assertIn("USD", result)

    def test_empty_query_has_actionable_help(self):
        self.assertIn("请输入", route_query("   "))


class ExchangeRateTests(OfflineCase):
    def setUp(self):
        super().setUp()
        os.environ["EXCHANGE_API_KEY"] = "AUDIT_TEST_KEY"

    def assert_unavailable(self, result):
        self.assertIn("未获取", result)
        self.assertNotIn("7.20", result)
        self.assertNotIn("AUDIT_TEST_KEY", result)
        self.assertNotIn("当前美元兑人民币汇率约为", result)

    def test_missing_key_returns_unavailable_without_a_fake_rate(self):
        del os.environ["EXCHANGE_API_KEY"]
        self.assert_unavailable(get_exchange_rate())

    def test_blank_key_does_not_make_a_request(self):
        os.environ["EXCHANGE_API_KEY"] = "  "
        self.assert_unavailable(get_exchange_rate())

    def test_success_reports_explicit_pair_and_source(self):
        with patch("src.tools.requests.get", return_value=response(successful_payload())) as http:
            result = get_exchange_rate()
        self.assertIn("1 USD = 7.12 CNY", result)
        self.assertIn("ExchangeRate-API", result)
        self.assertNotIn("实时", result)
        self.assertEqual(http.call_args.kwargs["timeout"], 10)

    def test_http_error_cannot_be_overridden_by_success_json(self):
        with patch("src.tools.requests.get", return_value=response(successful_payload(), 500)):
            self.assert_unavailable(get_exchange_rate())

    def test_redirect_is_not_treated_as_a_successful_quote(self):
        with patch("src.tools.requests.get", return_value=response(successful_payload(), 302)):
            self.assert_unavailable(get_exchange_rate())

    def test_provider_error_returns_unavailable(self):
        with patch("src.tools.requests.get", return_value=response({"result": "error", "error-type": "quota-reached"})):
            self.assert_unavailable(get_exchange_rate())

    def test_bad_json_returns_unavailable(self):
        result = response(None)
        result._content = b"<html>not JSON</html>"
        with patch("src.tools.requests.get", return_value=result):
            self.assert_unavailable(get_exchange_rate())

    def test_non_object_json_returns_unavailable(self):
        for payload in [None, [], "success", 42]:
            with self.subTest(payload=payload), patch("src.tools.requests.get", return_value=response(payload)):
                self.assert_unavailable(get_exchange_rate())

    def test_wrong_or_missing_base_currency_is_rejected(self):
        for base in ["CNY", None]:
            payload = successful_payload()
            payload["base_code"] = base
            with self.subTest(base=base), patch("src.tools.requests.get", return_value=response(payload)):
                self.assert_unavailable(get_exchange_rate())

    def test_missing_or_invalid_conversion_rates_are_rejected(self):
        for rates in [None, [], {}, "CNY: 7.12"]:
            payload = successful_payload()
            payload["conversion_rates"] = rates
            with self.subTest(rates=rates), patch("src.tools.requests.get", return_value=response(payload)):
                self.assert_unavailable(get_exchange_rate())

    def test_rate_must_be_a_positive_finite_number(self):
        for rate in [None, "7.12", True, 0, -7.12, float("nan"), float("inf"), float("-inf"), 10 ** 400]:
            with self.subTest(rate=rate), patch("src.tools.requests.get", return_value=response(successful_payload(rate))):
                self.assert_unavailable(get_exchange_rate())

    def test_timeout_does_not_expose_url_or_key(self):
        with patch("src.tools.requests.get", side_effect=requests.Timeout("https://example.invalid/AUDIT_TEST_KEY")):
            self.assert_unavailable(get_exchange_rate())

    def test_connection_failure_does_not_expose_url_or_key(self):
        with patch("src.tools.requests.get", side_effect=requests.ConnectionError("https://example.invalid/AUDIT_TEST_KEY")):
            self.assert_unavailable(get_exchange_rate())


class CliTests(OfflineCase):
    def run_cli(self, inputs):
        out = io.StringIO()
        with patch("builtins.input", side_effect=inputs), contextlib.redirect_stdout(out):
            try:
                main()
            except (EOFError, KeyboardInterrupt) as error:
                self.fail(f"CLI must exit cleanly, got {type(error).__name__}")
        return out.getvalue()

    def test_exit_accepts_surrounding_whitespace_and_case(self):
        self.assertIn("程序已退出", self.run_cli(["  EXIT  ", EOFError()]))

    def test_eof_exits_without_a_traceback(self):
        self.assertIn("程序已退出", self.run_cli([EOFError()]))

    def test_keyboard_interrupt_exits_without_a_traceback(self):
        self.assertIn("程序已退出", self.run_cli([KeyboardInterrupt()]))

    def test_keyboard_interrupt_during_http_exits_without_a_traceback(self):
        os.environ["EXCHANGE_API_KEY"] = "AUDIT_TEST_KEY"
        with patch("src.tools.requests.get", side_effect=KeyboardInterrupt):
            self.assertIn("程序已退出", self.run_cli(["USD/CNY", EOFError()]))

    def test_unknown_query_does_not_stop_the_loop(self):
        result = self.run_cli(["你好", "exit"])
        self.assertIn("时间", result)
        self.assertIn("程序已退出", result)


if __name__ == "__main__":
    unittest.main()
