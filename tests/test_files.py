from portfolio_intelligence.utils.paths import autodetect_file


def test_autodetect_file(tmp_path):
    file = tmp_path / "transactions.csv"
    file.write_text("date,amount\n2026-01-01,10\n")
    assert autodetect_file(tmp_path, ".csv", ("transaction",)) == file
