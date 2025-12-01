"""AI Assistant powered by OpenRouter for F1 data analysis."""
import os
import sys
from openai import OpenAI
import pandas as pd
from pathlib import Path
from typing import Optional
from functools import lru_cache

# Add parent directory to path for library imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from library.connection import connection_manager


@lru_cache(maxsize=1)
def get_dynamic_schema_context() -> str:
    """
    Dynamically fetch schema from Snowflake and build context for LLM.
    This ensures the AI always has up-to-date schema information.

    Cached to avoid repeated database queries (cache invalidates on app restart).
    """
    try:
        with connection_manager.get_connection(schema="ANALYTICS") as conn:
            cursor = conn.cursor()

            # Query to get all tables and columns in ANALYTICS schema
            query = """
            SELECT
                table_name,
                column_name,
                data_type,
                ordinal_position
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE table_schema = 'ANALYTICS'
            ORDER BY table_name, ordinal_position
            """

            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

        # Build schema context from results
        schema_by_table = {}
        for table_name, column_name, data_type, _ in results:
            if table_name not in schema_by_table:
                schema_by_table[table_name] = []
            schema_by_table[table_name].append(f"   - {column_name.lower()} ({data_type.lower()})")

        # Build formatted schema text
        schema_text = "You are an F1 data analyst assistant with access to a Snowflake database.\n\n"
        schema_text += "Available tables in ANALYTICS schema:\n\n"

        for i, (table_name, columns) in enumerate(schema_by_table.items(), 1):
            schema_text += f"{i}. {table_name.lower()}\n"
            schema_text += "\n".join(columns) + "\n\n"

        # Add domain-specific instructions
        schema_text += """
CRITICAL - Understanding "Latest/Last/Most Recent" Race:
- When user asks about "last race", "latest race", "most recent race"
- Use the race with MAX(date_start) from fct_race_results (NOT from ingested_at!)
- Example query for "who won the last race":

  SELECT driver_name, team_name, final_position, location, circuit_short_name, year, date_start
  FROM ANALYTICS.fct_race_results
  WHERE final_position = 1 AND session_name = 'Race'
  ORDER BY date_start DESC
  LIMIT 1

When generating SQL:
- ALWAYS use ANALYTICS schema explicitly (e.g., ANALYTICS.fct_race_results)
- DO NOT join with dim_drivers - all driver info is already in fct_race_results
- For race winners: WHERE final_position = 1 AND session_name = 'Race'
- For lap times: filter WHERE lap_duration > 0
- Lap times are in seconds (convert to minutes:seconds for display)

CRITICAL - Which table to use:
- Questions about "how many drivers" or "list all drivers" → USE dim_drivers (complete list of all drivers)
- Questions about race results, positions, winners → USE fct_race_results
- Questions about lap times, fastest laps, sectors → USE fct_lap_times
- DO NOT count drivers from fct_lap_times or fct_race_results - use dim_drivers for driver counts!
"""

        return schema_text

    except Exception as e:
        print(f"Error fetching dynamic schema: {e}")
        # Fallback to basic schema if introspection fails
        return "You are an F1 data analyst assistant. Generate SQL queries for the ANALYTICS schema."


def get_openrouter_client():
    """Get OpenRouter client configured to use OpenAI-compatible API."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        raise ValueError("OPENROUTER_API_KEY not set in .env file. Get your key from https://openrouter.ai/keys")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def get_ai_response(user_question: str, model: str = "openai/gpt-4o-mini") -> str:
    """
    Get AI response using OpenRouter.

    Args:
        user_question: User's question about F1 data
        model: Model to use (default: openai/gpt-3.5-turbo for cost efficiency)

    Returns:
        AI-generated response
    """
    try:
        client = get_openrouter_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly F1 expert talking to a regular fan. Answer questions naturally and conversationally in plain English."
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error communicating with AI: {str(e)}"


def generate_sql_from_question(user_question: str, model: str = "openai/gpt-4o-mini") -> Optional[str]:
    """
    Generate SQL query from natural language question.

    Args:
        user_question: Natural language question
        model: Model to use

    Returns:
        SQL query string or None if couldn't generate
    """
    # Get dynamic schema context from Snowflake
    schema_context = get_dynamic_schema_context()

    prompt = f"""Generate a Snowflake SQL query to answer this question: "{user_question}"

Return ONLY the SQL query, no explanation. The query should:
- Use the ANALYTICS schema
- Be valid Snowflake SQL
- Include appropriate JOINs if needed
- Filter out invalid data (e.g., lap_duration > 0)
- Be properly formatted

SQL Query:"""

    try:
        client = get_openrouter_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": schema_context
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        sql = response.choices[0].message.content.strip()

        # Clean up the SQL (remove markdown code blocks if present)
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]

        return sql.strip()

    except Exception as e:
        print(f"Error generating SQL: {e}")
        return None


def answer_question_from_data(question: str, results_df: pd.DataFrame, model: str = "openai/gpt-4o-mini") -> str:
    """
    Answer user's question in plain English based on query results.
    This is the ONLY function that should be called from app.py for data-based questions.

    Args:
        question: Original question from the user
        results_df: DataFrame with query results
        model: Model to use

    Returns:
        Plain English answer to the user's question (NO SQL, NO technical details)
    """
    # Limit rows for context (send max 10 rows)
    sample_data = results_df.head(10).to_string()

    prompt = f"""You are answering a question for a regular F1 fan (not a technical analyst).

User's question: "{question}"

Data from the database:
{sample_data}

CRITICAL INSTRUCTIONS:
- Answer the question directly in 2-4 sentences
- ALWAYS include the actual numbers, times, positions, and data from the results
- Use plain, conversational English
- NEVER mention SQL, queries, databases, or technical terms
- NEVER show or mention code
- NO fluff words like "amazing", "exciting", "impressive" - just state the facts and data
- If there are lap times in seconds, convert to minutes:seconds format (e.g., 92.5 seconds = 1:32.5)
- Be specific: include driver names, exact lap times, positions, points, team names, etc.
- Don't make assumptions - only use the data provided

Example good answer: "Max Verstappen won the race with a time of 1:32:15.123. He finished 5.2 seconds ahead of Lewis Hamilton who came in 2nd place."
Example bad answer: "Max Verstappen had an amazing performance and dominated the race!" (no data, just opinion)

Answer:"""

    try:
        client = get_openrouter_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a factual F1 data reporter. Always cite specific numbers, times, and data from the results. Never add subjective opinions or excitement. Just report the facts clearly and directly."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Sorry, I couldn't answer that question. {str(e)}"
