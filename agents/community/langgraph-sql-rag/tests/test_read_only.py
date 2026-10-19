import pytest

from langgraph_sql_rag.tools import ReadOnlyViolationError, validate_read_only_query


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM t",
        "select a, b from t where c = 'DROP TABLE x';",
        "SELECT update_date, created FROM t",
        'SELECT "DELETE" FROM t',
        "-- comment\nSELECT 1 FROM sysibm.sysdummy1",
        "WITH x AS (SELECT 1 AS a FROM t) SELECT a FROM x",
        "VALUES 1",
        "SELECT REPLACE(name, 'a', 'b') FROM t",
    ],
)
def test_read_only_queries_allowed(query):
    validate_read_only_query(query)


@pytest.mark.parametrize(
    "query",
    [
        "",
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET a = 1",
        "DELETE FROM t",
        "DROP TABLE t",
        "TRUNCATE TABLE t",
        "SELECT 1; DROP TABLE t",
        "/* hi */ DELETE FROM t",
        "WITH x AS (SELECT 1 FROM t) DELETE FROM t",
        "SELECT * FROM FINAL TABLE (INSERT INTO t VALUES (1))",
        "SELECT * INTO new_t FROM t",
        "CALL some_proc()",
    ],
)
def test_non_read_only_queries_rejected(query):
    with pytest.raises(ReadOnlyViolationError):
        validate_read_only_query(query)
