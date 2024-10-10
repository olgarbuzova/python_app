from typing import List

from pydantic import BaseModel


class TweetIn(BaseModel):
    tweet_data: str
    tweet_media_ids: List[int]
