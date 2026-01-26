import re


class BaseSQLDatabase:
    """
    Abstract base clas providing shared utility logic for SQL backends.
    """

    FORBIDDEN_KEYS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "VACUUM"}

    def __init__(self, read_only: bool = True) -> None:
        self.read_only = read_only

    def _is_write_query(self, query: str) -> bool:
        sql = query.upper().strip()

        # Strip leading SQL comments
        while sql.startswith("--") or sql.startswith("/*"):
            if sql.startswith("--"):
                sql = sql.split("\n", 1)[-1].lstrip()
            else:
                _, _, sql = sql.partition("*/")
                sql = sql.lstrip()

        # Collapse all whitespace and remove inline comments for safer detection

        sql_clean = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        sql_clean = re.sub(r"--.*", " ", sql_clean)
        sql_clean = " ".join(sql_clean.split())  # normalize whitespace

        # Check forbidden keywords at start or after a CTE
        if sql_clean.startswith("WITH"):
            # Remove the initial WITH clause up to the first semicolon or forbidden keyword
            # and see if any forbidden keyword appears next
            return any(kw in sql_clean for kw in self.FORBIDDEN_KEYS)

        return any(sql_clean.startswith(kw) for kw in self.FORBIDDEN_KEYS)

    # def format_results_as_markdown(self, result: QueryResult) -> str:
    #     """Standardizes how the LLM sees the data."""
    #     if not result.columns:
    #         return "Query executed successfully. No rows returned."

    #     header = "| " + " | ".join(result.columns) + " |"
    #     separator = "| " + " | ".join(["---"] * len(result.columns)) + " |"
    #     rows = []
    #     for row in result.rows:
    #         rows.append("| " + " | ".join(map(str, row)) + " |")

    #     return "\n".join([header, separator] + rows)
