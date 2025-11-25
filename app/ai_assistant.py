"""AI Assistant powered by local Ollama LLM for F1 data analysis."""
import ollama
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

2. dim_sessions - Session dimension table
   - session_key (int) - Primary key
   - session_name (string) - e.g., "Race", "Qualifying", "Sprint"
   - session_type (string) - Session category
   - year (int)
   - date_start (timestamp) - Actual race/session date
   - date_end (timestamp)
   - location (string)
   - country_name (string)
   - circuit_short_name (string)

3. fct_lap_times - Lap times fact table
   - session_key (int)
   - driver_number (int)
   - lap_number (int)
   - lap_duration (float) - in seconds
   - segment_1_duration, segment_2_duration, segment_3_duration (float)
   - is_pit_out_lap (boolean)
   - date_start (timestamp)

4. fct_race_results - Race results fact table
   - session_key (int)
   - driver_number (int)
   - position (int)
   - final_position (int)
   - points (int)
   - status (string)

IMPORTANT - Understanding "Latest/Last/Most Recent" Sessions:
- When user asks about "last race", "latest session", "most recent race", etc.
- Use MAX(date_start) from dim_sessions WHERE session_type = 'Race'
- DO NOT use ingested_at or any data load timestamps
- The "latest race" is based on the ACTUAL race date (date_start), not when data was loaded

When generating SQL:
- Always use ANALYTICS schema
- Table names: dim_drivers, dim_sessions, fct_lap_times, fct_race_results
- Join on driver_number and session_key
- ALWAYS JOIN with dim_sessions to get session names, dates, locations
- For "latest/last/most recent race" queries:
  - First find: SELECT session_key FROM dim_sessions WHERE session_type = 'Race' ORDER BY date_start DESC LIMIT 1
  - Then use that session_key in your main query
- Lap times are in seconds (divide by 60 for minutes)
- Filter out invalid laps: WHERE lap_duration > 0
"""


def get_ai_response(user_question: str, model: str = "llama3.1") -> str:
    """
    Get AI response using Ollama.
    
    Args:
        user_question: User's question about F1 data
        model: Ollama model to use (default: llama3.1)
    
    Returns:
        AI-generated response
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SCHEMA_CONTEXT
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ]
        )
        
        return response['message']['content']
        
    except Exception as e:
        return f"Error communicating with AI: {str(e)}. Make sure Ollama is running (`ollama serve`)."


def generate_sql_from_question(user_question: str, model: str = "llama3.1") -> Optional[str]:
    """
    Generate SQL query from natural language question.
    
    Args:
        user_question: Natural language question
        model: Ollama model to use
    
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
        response = ollama.chat(
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
        
        sql = response['message']['content'].strip()
        
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


def explain_results(question: str, results_df: pd.DataFrame, model: str = "llama3.1") -> str:
    """
    Answer user's question in plain English based on query results.

    Args:
        question: Original question from the user
        results_df: DataFrame with query results
        model: Ollama model to use

    Returns:
        Plain English answer to the user's question
    """
    # Limit rows for context (send max 10 rows)
    sample_data = results_df.head(10).to_string()

    prompt = f"""You are answering a question for a regular F1 fan (not a technical analyst).

User's question: "{question}"

Data from the database:
{sample_data}

INSTRUCTIONS:
- Answer the question directly in 1-3 clear sentences
- Use plain, conversational English
- NEVER mention SQL, queries, databases, or technical terms
- NEVER show or mention code
- Just answer what they asked as if you're having a normal conversation
- If there are lap times in seconds, convert to minutes:seconds format (e.g., 92.5 seconds = 1:32.5)

Answer:"""

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly F1 expert talking to a regular fan. Never use technical jargon or mention databases/SQL. Answer questions naturally and conversationally."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response['message']['content']

    except Exception as e:
        return f"Sorry, I couldn't answer that question. {str(e)}"
