import re

from database_pydantic_ai.types import TableInfo


class BaseSQLDatabase:
    """
    Abstract base class providing shared utility logic for SQL backends.
    """

    FORBIDDEN_KEYS = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "REPLACE",
        "VACUUM",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "COPY",
        "MERGE",
        "CALL",
        "DO",
    }

    def __init__(self, read_only: bool = True, echo: bool = False) -> None:
        self.read_only = read_only
        self.echo = echo

    def check_query_safety(self, query: str) -> str:
        """
        The single entry point for all query validations.

        Returns the prepared query string if all checks pass.
        Raises PermissionError or ValueError if validation fails.
        """
        prepared_query = self._prepare_query(query)

        if not prepared_query:
            raise ValueError("Query is empty or only contains comments.")

        # Perform individual checks
        self._check_singular_query(prepared_query)
        self._check_permissions(prepared_query)

        return prepared_query

    def _prepare_query(self, query: str) -> str:
        """Strips comments and normalizes whitespace."""
        # Strip block comments
        sql = re.sub(r"/\*.*?\*/", " ", query, flags=re.DOTALL)
        # Strip line comments
        sql = re.sub(r"--.*", " ", sql)
        # Normalize whitespace
        return " ".join(sql.split()).strip()

    def _check_singular_query(self, cleaned_query: str) -> None:
        """Ensures only one SQL statement is present."""
        if ";" in cleaned_query.rstrip(";"):
            raise PermissionError("Multiple statements are not allowed for security reasons.")

    def _check_permissions(self, cleaned_query: str) -> None:
        """Enforces read-only restrictions if enabled."""
        if not self.read_only:
            return

        upper_sql = cleaned_query.upper()

        # Handle CTEs by checking the whole string for forbidden keywords
        if upper_sql.startswith("WITH"):
            if any(kw in upper_sql for kw in self.FORBIDDEN_KEYS):
                raise PermissionError("Write operation detected inside CTE in read-only mode.")

        # Handle standard queries by checking the starting keyword
        elif any(upper_sql.startswith(kw) for kw in self.FORBIDDEN_KEYS):
            raise PermissionError("Write operation denied. Database is in read-only mode.")

    # LEGACY PART EXCHANGED FOR NEW
    # def _is_write_query(self, query: str) -> bool:
    #     """Legacy support/Utility: Returns True if query contains write keywords."""
    #     try:
    #         self._check_permissions(self._prepare_query(query))
    #         return False
    #     except PermissionError:
    #         return True

    # TODO discuss if validator is needed for future purposes
    # def _is_valid_identifier(self, table_name: str) -> str:
    #     if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
    #         raise ValueError(f"Invalid SQL identifier: {table_name}")
    #     return table_name

    # TODO discuss if markdown return is scheduled
    def render_table_as_markdown(self, table: TableInfo) -> str:
        """Standardizes how the LLM sees the data."""

        # Build the components in a flat list of strings
        components = []
        components.append(f"#### {table.name} ####")

        # Extract column names for the header
        column_names = list(table.columns[0].model_dump().keys()) + ["foreign_key"]
        components.append("| " + " | ".join(column_names) + " | |")

        # Add the spacer (must be below the header)
        components.append("| " + " | ".join(["---"] * len(column_names)) + " |")

        # Build FK map
        fk_map = {f.column: f"{f.references_table}({f.references_column})" for f in table.foreign_keys or []}

        # Add the rows
        for col in table.columns:
            row_values = [str(v) for v in col.model_dump().values()]
            row_str = f"| {' | '.join(row_values)}"
            row_str += f" | {fk_map[col.name]} |" if col.name in fk_map else " | |"
            components.append(row_str)

        # Join everything exactly once
        return "\n".join(components)
