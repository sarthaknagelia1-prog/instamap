"""
tests/test_multi_source_adapters.py

Tests for multi-source data ingestion:
- JSONAdapter (direct JSON, wrapped objects)
- PasteAdapter (TSV, Excel/Sheets copy-paste, Markdown tables)
- CSVAdapter (delimiter sniffing for comma, tab, semicolon)
- Source platform detection (Sprout, Hootsuite, Later, Meta)
- New ingestion endpoints (/data/csv-template, /data/sources, /data/ingest/paste)
"""

from backend.data.adapters.csv_adapter import CSVAdapter
from backend.data.adapters.json_adapter import JSONAdapter
from backend.data.adapters.paste_adapter import PasteAdapter
from backend.data.schema_mapper import detect_source_platform


def test_json_adapter_list_and_wrapped():
    adapter = JSONAdapter()

    # Raw list
    data_list = [{"id": "p1", "type": "reel", "likes": 50}]
    assert adapter.fetch(data=data_list) == data_list

    # Wrapped object {"posts": [...]}
    wrapped_posts = {"posts": [{"id": "p2", "type": "image", "likes": 30}]}
    assert len(adapter.fetch(data=wrapped_posts)) == 1
    assert adapter.fetch(data=wrapped_posts)[0]["id"] == "p2"

    # From JSON string
    json_str = '{"data": [{"id": "p3", "type": "carousel", "likes": 100}]}'
    res = adapter.fetch(content=json_str)
    assert len(res) == 1
    assert res[0]["id"] == "p3"


def test_paste_adapter_tsv_spreadsheet():
    adapter = PasteAdapter()
    tsv_text = "post_id\tdate\ttype\tlikes\tcomments\np_tsv1\t2026-10-01T12:00:00Z\treel\t200\t25\np_tsv2\t2026-10-02T12:00:00Z\timage\t150\t15"
    records = adapter.fetch(text=tsv_text)
    assert len(records) == 2
    assert records[0]["post_id"] == "p_tsv1"
    assert records[0]["type"] == "reel"
    assert records[1]["likes"] == "150"


def test_paste_adapter_markdown_table():
    adapter = PasteAdapter()
    md_text = (
        "| post_id | type | likes | comments |\n"
        "| --- | --- | --- | --- |\n"
        "| md_1 | reel | 500 | 45 |\n"
        "| md_2 | carousel | 300 | 20 |\n"
    )
    records = adapter.fetch(text=md_text)
    assert len(records) == 2
    assert records[0]["post_id"] == "md_1"
    assert records[1]["likes"] == "300"


def test_csv_adapter_delimiter_detection():
    adapter = CSVAdapter()

    # Semicolon separated
    semicolon_csv = "post_id;type;likes;comments\np_semi;reel;80;10"
    res_semi = adapter.fetch(content=semicolon_csv)
    assert len(res_semi) == 1
    assert res_semi[0]["post_id"] == "p_semi"
    assert res_semi[0]["likes"] == "80"

    # Tab separated
    tab_csv = "post_id\ttype\tlikes\tcomments\np_tab\tcarousel\t95\t12"
    res_tab = adapter.fetch(content=tab_csv)
    assert len(res_tab) == 1
    assert res_tab[0]["post_id"] == "p_tab"


def test_source_platform_detection():
    assert detect_source_platform(["Lifetime Post Total Reach", "Comments"]) == "sprout_social"
    assert detect_source_platform(["Date (GMT)", "Total Impressions"]) == "hootsuite"
    assert detect_source_platform(["Accounts Reached", "Publish time"]) == "meta_business_suite"
    assert detect_source_platform(["Permalink", "Reactions"]) == "later"
    assert detect_source_platform(["post_id", "likes"]) == "generic_csv_or_table"


def test_api_sources_and_template_endpoints(client):
    res_template = client.get("/data/csv-template")
    assert res_template.status_code == 200
    assert "post_id,date,type,likes" in res_template.text

    res_sources = client.get("/data/sources")
    assert res_sources.status_code == 200
    data = res_sources.json()
    assert "supported_input_methods" in data
    assert "compatible_platforms" in data


def test_api_paste_ingestion(client):
    tsv_paste = (
        "post_id\tdate\ttype\tlikes\tcomments\n"
        "paste_p1\t2026-10-01T10:00:00Z\treel\t300\t25\n"
        "paste_p2\t2026-10-02T10:00:00Z\tcarousel\t210\t18\n"
    )
    payload = {
        "creator_id": "creator_paste_test",
        "text_data": tsv_paste,
        "quality_threshold": 0.5,
    }
    res = client.post("/data/ingest/paste", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["data_ready"] is True
    assert data["inserted_count"] == 2
