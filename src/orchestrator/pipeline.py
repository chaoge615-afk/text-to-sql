"""Main orchestration pipeline for Text-to-SQL Multi-Agent System."""

import json
from typing import Dict, Any, Tuple, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.intent_agent import IntentAgent
from src.agents.schema_agent import SchemaAgent
from src.agents.sql_gen_agent import SQLGenAgent
from src.agents.review_agent import ReviewAgent
from src.database.duckdb_utils import execute_sql
from src.config import MAX_RETRIES


class TextToSQLPipeline:
    """Main pipeline orchestrating all agents."""

    def __init__(self):
        self.intent_agent = IntentAgent()
        self.schema_agent = SchemaAgent()
        self.sql_gen_agent = SQLGenAgent()
        self.review_agent = ReviewAgent()

    def format_result(self, query_result: list, question: str, sql: str) -> str:
        """Format query result into natural language response."""
        if not query_result:
            return "No data found."

        # Simple formatting for common cases
        if len(query_result) == 1:
            value = query_result[0]
            if isinstance(value, (int, float)):
                return f"Result: {value}"
            return f"Result: {value}"
        else:
            lines = ["Result:"]
            for row in query_result:
                lines.append(f"  {row}")
            return "\n".join(lines)

    def run(self, question: str) -> Dict[str, Any]:
        """
        Run the full pipeline for a user question.

        Returns:
            Dict with keys: success, sql, result, answer, error, iterations
        """
        iterations = 0
        last_error = None

        while iterations < MAX_RETRIES:
            iterations += 1

            # Step 1: Intent Understanding
            intent = self.intent_agent.run(question)
            if "error" in intent:
                return {
                    "success": False,
                    "error": f"Intent parsing failed: {intent['error']}",
                    "iterations": iterations,
                }

            # Step 2: Schema Retrieval
            schema = self.schema_agent.run(intent)
            if "error" in schema:
                return {
                    "success": False,
                    "error": f"Schema retrieval failed: {schema['error']}",
                    "iterations": iterations,
                }

            # Step 3: SQL Generation
            sql_result = self.sql_gen_agent.run(intent, schema)
            if "error" in sql_result:
                return {
                    "success": False,
                    "error": f"SQL generation failed: {sql_result['error']}",
                    "iterations": iterations,
                }

            sql = sql_result.get("sql", "")
            if not sql:
                return {
                    "success": False,
                    "error": "No SQL generated",
                    "iterations": iterations,
                }

            # Step 4: SQL Review
            review = self.review_agent.run(sql, intent, schema)
            if review.get("passed", False):
                # SQL passed review, execute it
                try:
                    query_result = execute_sql(sql)
                    answer = self.format_result(query_result, question, sql)
                    return {
                        "success": True,
                        "sql": sql,
                        "result": query_result,
                        "answer": answer,
                        "iterations": iterations,
                    }
                except Exception as e:
                    last_error = f"SQL execution failed: {e}"
                    # Continue to retry with new generation
            else:
                # SQL failed review, get error info
                issues = review.get("issues", [])
                error_msgs = [f"- {issue['description']} (suggestion: {issue.get('suggestion', 'N/A')})" for issue in issues]
                last_error = f"SQL review failed:\n" + "\n".join(error_msgs)

            # If we get here, retry with a hint to fix the issues
            if iterations < MAX_RETRIES:
                # Could inject the error into the next iteration via context
                pass

        # Max retries exceeded
        return {
            "success": False,
            "sql": sql if 'sql' in dir() else None,
            "error": f"Max retries ({MAX_RETRIES}) exceeded. Last error: {last_error}",
            "iterations": iterations,
        }


def query(question: str) -> Dict[str, Any]:
    """Convenience function to run a single query."""
    pipeline = TextToSQLPipeline()
    return pipeline.run(question)
