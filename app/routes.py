import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Annotated, Dict

from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import defaultload, joinedload, load_only, subqueryload
from starlette import status

from app.database import session
from app.models import Media, Tweet, User, likes_table, user_following
from app.schemas import TweetIn
from app.security import check_authentication_key

RESULT_TRUE = {"result": True}
MEDIA_DIR = "./medias/"


def create_routes(app):
    @app.post("/api/auth")
    def result(
        auth: Annotated[dict, Depends(check_authentication_key)]
    ) -> Dict:
        """Getting authentication result"""
        query = select(User).where(User.id == auth.get("user_id"))
        user = session.scalar(query)
        return user

    @app.post("/api/tweets")
    async def add_new_tweet(
        auth: Annotated[dict, Depends(check_authentication_key)], tweet: TweetIn
    ) -> Dict:
        """Add a new tweet"""
        user_id = auth.get("user_id")
        try:
            query = (
                insert(Tweet)
                .values(content=tweet.tweet_data, author_id=user_id)
                .returning(Tweet.id)
            )
            tweet_id = session.execute(query).fetchone()
            session.commit()

            if tweet_id:
                id = tweet_id[0]
                update_query = (
                    update(Media)
                    .where(Media.id.in_(tweet.tweet_media_ids))
                    .values(tweet_id=id)
                )
                session.execute(update_query)
                session.commit()
                return {"tweet_id": id} | RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.post("/api/medias")
    async def add_media_files(
        auth: Annotated[dict, Depends(check_authentication_key)],
        file: UploadFile,
    ) -> Dict:
        """Upload files from tweet"""
        filename = f"{int(datetime.timestamp(datetime.now()))}-{file.filename}"
        filename_path = Path(os.path.join(MEDIA_DIR, filename))

        with filename_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        try:
            query = (
                insert(Media)
                .values(link=f"medias/{filename}")
                .returning(Media.id)
            )
            media_id = session.execute(query).fetchone()
            session.commit()
            if media_id:
                id = media_id[0]
                return {"media_id": id} | RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.delete("/api/tweets/{tweet_id}")
    async def delete_tweet_by_id(
        auth: Annotated[dict, Depends(check_authentication_key)], tweet_id: int
    ) -> Dict:
        """Delete tweet by id"""
        user_id = auth.get("user_id")
        try:
            query = select(Tweet).where(Tweet.id == tweet_id)
            tweet = session.execute(query).unique()
            tweet = tweet.scalar_one()
            if tweet.author_id == user_id:
                session.delete(tweet)
                session.commit()
                return RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.post("/api/tweets/{tweet_id}/likes")
    async def add_like(
        auth: Annotated[dict, Depends(check_authentication_key)], tweet_id: int
    ) -> Dict:
        """Add like to tweet"""
        user_id = auth.get("user_id")
        try:
            query = (
                insert(likes_table)
                .values(user_id=user_id, tweet_id=tweet_id)
                .returning(likes_table.c.tweet_id)
            )
            result = session.execute(query).fetchone()
            session.commit()
            if result:
                return RESULT_TRUE
            else:
                session._transaction.rollback()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect data",
            )

    @app.delete("/api/tweets/{tweet_id}/likes")
    async def delete_like(
        auth: Annotated[dict, Depends(check_authentication_key)], tweet_id: int
    ) -> Dict:
        """Delete like to tweet"""
        user_id = auth.get("user_id")
        try:
            query = (
                delete(likes_table)
                .where(
                    likes_table.c.tweet_id == tweet_id,
                    likes_table.c.user_id == user_id,
                )
                .returning(likes_table.c.tweet_id)
            )
            deleted_like = session.execute(query).fetchone()
            session.commit()
            if deleted_like:
                return RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.post("/api/users/{user_id}/follow")
    async def follow_user(
        auth: Annotated[dict, Depends(check_authentication_key)], user_id: int
    ) -> Dict:
        """Follow another user by user id"""
        follower_id = auth.get("user_id")
        try:
            query = (
                insert(user_following)
                .values(user_id=user_id, follower_id=follower_id)
                .returning(user_following.c.user_id)
            )
            result = session.execute(query).fetchone()
            session.commit()
            if result:
                return RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.delete("/api/users/{user_id}/follow")
    async def unfollow_user(
        auth: Annotated[dict, Depends(check_authentication_key)], user_id: int
    ) -> Dict:
        """Unfollow another user by user id"""
        follower_id = auth.get("user_id")
        try:
            query = (
                delete(user_following)
                .where(
                    user_following.c.user_id == user_id,
                    user_following.c.follower_id == follower_id,
                )
                .returning(user_following.c.user_id)
            )
            deleted_following = session.execute(query).fetchone()
            session.commit()
            if deleted_following:
                return RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.get("/api/tweets")
    async def get_tweet_feed(
        auth: Annotated[dict, Depends(check_authentication_key)]
    ) -> Dict:
        """Get tweet feed"""
        try:
            query = select(Tweet).options(joinedload(Tweet.attachments))
            tweets = session.scalars(query).unique().all()
            tweets_new = [
                {
                    "id": tw.id,
                    "author_id": tw.author_id,
                    "content": tw.content,
                    "author": tw.author,
                    "attachments": [ta.link for ta in tw.attachments],
                    "likes": [
                        {"user_id": tl.id, "name": tl.name} for tl in tw.likes
                    ],
                }
                for tw in tweets
            ]
            return {"tweets": tweets_new} | RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.get("/api/users/me")
    async def get_info_about_yourself(
        auth: Annotated[dict, Depends(check_authentication_key)]
    ) -> Dict:
        """Get information about yourself"""
        user_id = auth.get("user_id")
        try:
            query = (
                select(User)
                .options(joinedload(User.followers), joinedload(User.following))
                .where(User.id == user_id)
            )
            user = session.scalar(query)
            return {"user": user} | RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    @app.get("/api/users/{user_id}")
    async def get_info_by_id(
        user_id: int, auth: Annotated[dict, Depends(check_authentication_key)]
    ) -> Dict:
        """Get information anouther user by user id"""
        try:
            query = (
                select(User)
                .options(joinedload(User.followers), joinedload(User.following))
                .where(User.id == user_id)
            )
            user = session.scalar(query)
            return {"user": user} | RESULT_TRUE
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
