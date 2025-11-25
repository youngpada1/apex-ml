"""AI Assistant powered by OpenRouter for F1 data analysis."""
import os
from openai import OpenAI
import pandas as pd
from typing import Optional

# Database schema information for context
SCHEMA_CONTEXT = """
You are an F1 data analyst assistant with access to a Snowflake database.

Available tables in ANALYTICS schema:

1. dim_drivers - Driver dimension table
   - driver_number (int)
   - full_name (string)
   - name_acronym (string)
   - team_name (string)
   - team_colour (string)
   - country_code (string)

2. fct_lap_times - Lap times fact table
   - session_key (int)
   - driver_number (int)
   - lap_number (int)
   - lap_duration (float) - in seconds
   - segment_1_duration, segment_2_duration, segment_3_duration (float)
   - is_pit_out_lap (boolean)
   - date_start (timestamp) - ACTUAL race date (use this for "latest/last race")

3. fct_race_results - Race results fact table (ONLY for Race sessions)
   - session_key (int)
   - driver_number (int)
   - driver_name (string) - Full driver name
   - team_name (string)
   - final_position (int) - Final position in race (1 = winner, 2 = 2nd place, etc.)
   - session_name (string) - e.g., "Race"
   - circuit_short_name (string)
   - location (string)
   - year (int)
   - date_start (timestamp) - ACTUAL race date (use this for "latest/last race")

CRITICAL - Understanding "Latest/Last/Most Recent" Race:
- When user asks about "last race", "latest race", "most recent race"
- Use the race with MAX(date_start) from fct_race_results (NOT from ingested_at!)
- Example query for "who won the last race" (COPY THIS EXACTLY):

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
- IMPORTANT: fct_race_results already has driver_name and team_name - no need to join
"""


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
                    "content": SCHEMA_CONTEXT
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
