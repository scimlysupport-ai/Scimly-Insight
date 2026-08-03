import pandas as pd

from app.services.analysis_service import generate_ai_insights


def test_generate_ai_insights_creates_text_only_summary():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]),
            "revenue": [100, 120, 90, 130],
            "customer": ["Alice", "Bob", "Alice", "Carol"],
            "product": ["Widget", "Gadget", "Widget", "Doodad"],
        }
    )

    insights = generate_ai_insights(df)

    assert len(insights) == 5
    assert any("Revenue increased" in item["text"] for item in insights)
    assert any("Highest sales" in item["title"] for item in insights)
    assert any("Top customer" in item["title"] for item in insights)
    assert any("Best product" in item["title"] for item in insights)
    assert any("Worst month" in item["title"] for item in insights)
