import pandas as pd
import pytest

from app.services.ai_chat_service import build_ai_chat_widget


@pytest.fixture
def retail_df():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.DataFrame({
        "date": dates,
        "revenue": [100 + i for i in range(60)],
        "category": (["Electronics", "Home", "Clothing"] * 20),
        "region": (["West", "East", "North", "South"] * 15),
        "customer": [f"Customer {i % 10}" for i in range(60)],
    })


@pytest.fixture
def hr_df():
    return pd.DataFrame({
        "hire_date": pd.date_range("2022-01-01", periods=40, freq="W"),
        "department": (["Sales", "Engineering", "Support", "HR"] * 10),
        "salary": [50000 + i * 500 for i in range(40)],
        "attrition": (["No"] * 32 + ["Yes"] * 8),
    })


@pytest.fixture
def banking_df():
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=30, freq="D"),
        "amount": [200 + i * 5 for i in range(30)],
        "payment_method": (["Card", "Cash", "Wallet"] * 10),
    })


def test_monthly_revenue(retail_df):
    widget = build_ai_chat_widget(retail_df, "Show monthly revenue.")
    assert widget["chart"] == "line"
    assert widget["x"] == "date"
    assert widget["y"] == "revenue"
    assert "SELECT" in widget["sql"]
    assert len(widget["data"]) > 0


def test_which_region_highest_sales(retail_df):
    widget = build_ai_chat_widget(retail_df, "Which region generated the highest sales?")
    assert widget["chart"] == "bar"
    assert widget["x"] == "region"
    assert widget["y"] == "revenue"
    assert len(widget["data"]) == 4
    # sorted descending, so the "highest" region is first
    assert widget["data"][0]["value"] >= widget["data"][-1]["value"]


def test_top_customers_by_revenue(retail_df):
    widget = build_ai_chat_widget(retail_df, "Top 10 customers by revenue.")
    assert widget["chart"] == "table"
    assert widget["entity_column"] == "customer"
    assert widget["measure"] == "revenue"
    assert len(widget["data"]["rows"]) <= 10


def test_compare_sales_by_category(retail_df):
    widget = build_ai_chat_widget(retail_df, "Compare sales by category.")
    assert widget["chart"] in ("bar", "pie")
    assert widget["x"] == "category"
    assert widget["y"] == "revenue"


def test_summarize_dataset(retail_df):
    widget = build_ai_chat_widget(retail_df, "Summarize this dataset.")
    assert widget["chart"] == "insights"
    assert len(widget["data"]["insights"]) > 0


def test_attrition_by_department(hr_df):
    widget = build_ai_chat_widget(hr_df, "Show attrition by department.")
    assert widget["chart"] == "bar"
    assert widget["x"] == "department"
    assert widget["rate_column"] == "attrition"
    # a rate, not a headcount -- every value should be a valid percentage
    assert all(0 <= point["value"] <= 100 for point in widget["data"])


def test_average_salary(hr_df):
    widget = build_ai_chat_widget(hr_df, "What is the average salary?")
    assert widget["chart"] == "kpi"
    assert widget["column"] == "salary"
    assert widget["agg"] == "avg"
    assert widget["data"]["value"] == pytest.approx(hr_df["salary"].mean())


def test_daily_transaction_trend(banking_df):
    widget = build_ai_chat_widget(banking_df, "Display daily transaction trend.")
    assert widget["chart"] == "line"
    assert widget["x"] == "date"
    assert widget["granularity"] == "day"


def test_most_used_payment_method(banking_df):
    widget = build_ai_chat_widget(banking_df, "Which payment method is most used?")
    assert widget["chart"] == "bar"
    assert widget["x"] == "payment_method"
    assert len(widget["data"]) > 0


def test_booking_status_distribution():
    df = pd.DataFrame({
        "booking_status": (["Confirmed", "Cancelled", "Pending"] * 10),
        "amount": list(range(30)),
    })
    widget = build_ai_chat_widget(df, "Show booking status distribution.")
    assert widget["chart"] == "pie"
    assert widget["x"] == "booking_status"


def test_unmatched_prompt_falls_back_to_table(retail_df):
    widget = build_ai_chat_widget(retail_df, "asdkjashdkjashd nonsense query")
    assert widget["chart"] == "table"
    assert "data" in widget
