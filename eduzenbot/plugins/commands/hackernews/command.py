"""
hn - get_hackernews
"""

import logging
from enum import Enum
from types import SimpleNamespace
from typing import Any

import requests
from cachetools import TTLCache, cached
from telegram import ChatAction, Update
from telegram.ext import CallbackContext

from eduzenbot.decorators import create_user

session = requests.Session()

logger = logging.getLogger("rich")


class STORIES(Enum):
    """
    The types of stories that can be retrieved.
    """

    TOP = "topstories"
    NEW = "newstories"
    BEST = "beststories"
    ASK = "askstories"
    JOBS = "jobstories"

    def __str__(self) -> str:
        return self.value


def get_top_stories(
    story_type: STORIES = STORIES.TOP, limit: int | None = 10
) -> list[Any]:
    """
    Get the top stories from hackernews.

    :param limit: The number of stories to get.
    :return: A list of stories.
    """
    if story_type not in STORIES:
        raise ValueError(f"Invalid story type: {story_type}")

    url = f"https://hacker-news.firebaseio.com/v0/{story_type}.json"
    response = session.get(url)
    response.raise_for_status()
    return response.json()[:limit]


def get_item(id: int) -> dict[Any, Any]:
    """
    Get the story with the given id.

    :param id: The id of the story.
    :return: A dictionary containing the story.
    """
    url = f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
    response = session.get(url)
    response.raise_for_status()
    return response.json()


def get_hackernews_help(story_type: STORIES = STORIES.TOP) -> str:
    return f"*{str(story_type).capitalize()} stories from* [HackerNews](https://news.ycombinator.com)\n\n"


def parse_hackernews(story_id: int) -> str:
    raw_story = get_item(story_id)
    story = SimpleNamespace(**raw_story)
    # now = pendulum.now()
    # date = now - pendulum.from_timestamp(story.time)
    try:
        url = story.url
    except AttributeError:
        url = ""
    story_text = (
        f"[{story.title}]({url})"  # Score: {story.score} Hace: {date.in_words()}"
    )
    return story_text


@cached(cache=TTLCache(maxsize=1024, ttl=10800))
def hackernews(story_type: STORIES = STORIES.TOP, limit: int = 5) -> str:
    text_stories = []
    for story_id in get_top_stories(story_type, limit):
        try:
            story = parse_hackernews(story_id)
            text_stories.append(story)
        except Exception as e:
            logger.exception(e)
            continue

    # title = get_hackernews_help(story_type=story_type)
    title = "Stories from [HackerNews](https://news.ycombinator.com)\n"
    return title + "\n".join(text_stories)


@create_user
def get_hackernews(update: Update, context: CallbackContext) -> None:
    """
    Get the top stories from hackernews.

    :param limit: The number of stories to get.
    :return: A list of stories.
    """
    chat_id = update.effective_chat.id  # type: ignore
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)  # type: ignore

    type_story = context.args
    if type_story:
        text = hackernews(type_story)
    else:
        text = hackernews()

    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
