from dotenv import load_dotenv
from movie_functions import *
import chainlit as cl
import json

load_dotenv()

# Note: If switching to LangSmith, uncomment the following, and replace @observe with @traceable
# from langsmith.wrappers import wrap_openai
# from langsmith import traceable
# client = wrap_openai(openai.AsyncClient())

from langfuse.decorators import observe
from langfuse.openai import AsyncOpenAI
 
client = AsyncOpenAI()

gen_kwargs = {
    "model": "gpt-4o",
    "temperature": 0.2,
    "max_tokens": 500
}

SYSTEM_PROMPT = """\
You are a pirate.  You have access to The Movie Database (TMDB) API and can make
function calls to this API to answer movie related questions.  When discussing
movies, use the following rules:

1)  Use your knowledge:  If a user asks a general movie-related question that
you know the answer to, respond directly using your own knowledge base.Examples:
"Who directed Inception?"
"What are some top sci-fi movies from the 1990s?"
2)  When the user asks for current movies, use the get_now_playing_movies function.
3)  When the user asks for current showtimes, use the get_showtimes function.
4)  When the user asks for reviews, use the get_reviews function.
5)  When the user asks to purchase a ticket, use the buy_ticket function.
6)  After a function call, the function's response will be passed to you as a system message.  Look at the function return value and respond to the user.

To make a function call, create a JSON block of text similar to the following examples:

get_now_playing_movies example:
{
  "function":"get_now_playing_movies"
}

get_showtimes example:
{
  "function":"get_showtimes",
  "title":"<MOVIE TITLE>",
  "location":"<LOCATION>"
}

buy_ticket example:
{
  "function":"buy_ticket",
  "theater":"<THEATER NAME>",
  "movie":"<MOVIE TITLE>",
  "showtime":"<TIME>",
}

get_reviews example:
{
  "function":"get_reviews",
  "movie":"<MOVIE TITLE>"
}

When sending a function call, there must be no extra text around it. Only the JSON function.
"""

#Use the TMDB Function: When a user requests specific or up-to-date information about a movie or a list of movies (e.g., latest releases, trending films, or details on an obscure title), and you do not have that information or the data might have changed, call the TMDB function to fetch the required data.Examples:
#"What's the latest popular movie?"
#"Can you get details on Dune (2021)?"
#"Show me movies starring Tom Hanks."

@observe
@cl.on_chat_start
def on_chat_start():    
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    cl.user_session.set("message_history", message_history)

@observe
async def generate_response(client, message_history, gen_kwargs):
    response_message = cl.Message(content="")
    await response_message.send()

    stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)
    
    await response_message.update()

    return response_message

@cl.on_message
@observe
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])
    message_history.append({"role": "user", "content": message.content})
    
    response_message = await generate_response(client, message_history, gen_kwargs)

    try:
        function_call = json.loads(response_message.content)
        if "function" in function_call and function_call["function"] == "get_now_playing_movies":
            current_movies = get_now_playing_movies()
            message_history.append({"role": "system", "content": current_movies})
            response_message = await generate_response(client, message_history, gen_kwargs)
        if "function" in function_call and function_call["function"] == "get_showtimes":
            showtimes = get_showtimes(function_call["title"], function_call["location"])
            message_history.append({"role": "system", "content": showtimes})
            response_message = await generate_response(client, message_history, gen_kwargs)
    except json.JSONDecodeError:
        pass


    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)

if __name__ == "__main__":
    cl.main()
