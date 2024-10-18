import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Annotated, Dict

from fastapi import Depends, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session, joinedload
from starlette import status

from app.database import get_db
from app.models import Media, Tweet, User, likes_table, user_following
from app.schemas import TweetIn
from app.security import check_authentication_key

RESULT_TRUE = {"result": True}
MEDIA_DIR = "./medias/"


def create_routes(app):
    @app.post("/api/auth")
    def result(
        auth: Annotated[dict, Depends(check_authentication_key)],
        db: Session = Depends(get_db),
    ):
        """Getting authentication result"""
        query = select(User).where(User.id == auth.get("user_id"))
        user = db.scalar(query)
        return user

    @app.post("/api/tweets")
    async def add_new_tweet(
        auth: Annotated[dict, Depends(check_authentication_key)],
        tweet: TweetIn,
        db: Session = Depends(get_db),
    ):
        """Add a new tweet"""
        user_id = auth.get("user_id")
        try:
            query = (
                insert(Tweet)
                .values(content=tweet.tweet_data, author_id=user_id)
                .returning(Tweet.id)
            )
            tweet_id = db.execute(query).fetchone()
            db.commit()

            if tweet_id:
                id = tweet_id[0]
                update_query = (
                    update(Media)
                    .where(Media.id.in_(tweet.tweet_media_ids))
                    .values(tweet_id=id)
                )
                db.execute(update_query)
                db.commit()
                return {"tweet_id": id} | RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect data"
            )

    @app.post("/api/medias")
    async def add_media_files(
        auth: Annotated[dict, Depends(check_authentication_key)],
        file: UploadFile,
        db: Session = Depends(get_db),
    ):
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
            media_id = db.execute(query).fetchone()
            db.commit()
            if media_id:
                id = media_id[0]
                return {"media_id": id} | RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect data"
            )

    @app.delete("/api/tweets/{tweet_id}")
    async def delete_tweet_by_id(
        auth: Annotated[dict, Depends(check_authentication_key)],
        tweet_id: int,
        db: Session = Depends(get_db),
    ):
        """Delete tweet by id"""
        user_id = auth.get("user_id")
        try:
            query = select(Tweet).where(Tweet.id == tweet_id)
            tweet = db.scalars(query).one()
            if tweet.author_id == user_id:
                db.delete(tweet)
                db.commit()
                return RESULT_TRUE
            else:
                raise Exception
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect data"
            )

    @app.post("/api/tweets/{tweet_id}/likes")
    async def add_like(
        auth: Annotated[dict, Depends(check_authentication_key)],
        tweet_id: int,
        db: Session = Depends(get_db),
    ):
        """Add like to tweet"""
        user_id = auth.get("user_id")
        try:
            query = (
                insert(likes_table)
                .values(user_id=user_id, tweet_id=tweet_id)
                .returning(likes_table.c.tweet_id)
            )
            result = db.execute(query).fetchone()
            db.commit()
            if result:
                return RESULT_TRUE
            # else:
            #     db._transaction.rollback()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect data",
            )

    @app.delete("/api/tweets/{tweet_id}/likes")
    async def delete_like(
        auth: Annotated[dict, Depends(check_authentication_key)],
        tweet_id: int,
        db: Session = Depends(get_db),
    ):
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
            deleted_like = db.execute(query).fetchone()
            db.commit()
            if deleted_like:
                return RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect data"
            )

    @app.post("/api/users/{user_id}/follow")
    async def follow_user(
        auth: Annotated[dict, Depends(check_authentication_key)],
        user_id: int,
        db: Session = Depends(get_db),
    ):
        """Follow another user by user id"""
        follower_id = auth.get("user_id")
        try:
            query = (
                insert(user_following)
                .values(user_id=user_id, follower_id=follower_id)
                .returning(user_following.c.user_id)
            )
            result = db.execute(query).fetchone()
            db.commit()
            if result:
                return RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect data"
            )

    @app.delete("/api/users/{user_id}/follow")
    async def unfollow_user(
        auth: Annotated[dict, Depends(check_authentication_key)],
        user_id: int,
        db: Session = Depends(get_db),
    ):
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
            deleted_following = db.execute(query).fetchone()
            db.commit()
            if deleted_following:
                return RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect data"
            )

    @app.get("/api/tweets")
    async def get_tweet_feed(
        auth: Annotated[dict, Depends(check_authentication_key)],
        db: Session = Depends(get_db),
    ):
        """Get tweet feed"""
        user_id = auth.get("user_id")
        try:
            query = select(Tweet).options(joinedload(Tweet.attachments))
            tweets = db.scalars(query).unique().all()
            tweets_sorter_likes = sorted(
                tweets, key=lambda x: len(x.likes), reverse=True
            )
            tweets_sorter_follower = sorted(
                tweets_sorter_likes,
                key=lambda x: (
                    True
                    if user_id in [u.id for u in x.author.followers]
                    else False
                ),
                reverse=True,
            )
            tweets_result = [
                {
                    "id": tw.id,
                    "content": tw.content,
                    "attachments": [ta.link for ta in tw.attachments],
                    "author": {"id": tw.author.id, "name": tw.author.name},
                    "likes": [
                        {"user_id": tl.id, "name": tl.name} for tl in tw.likes
                    ],
                }
                for tw in tweets_sorter_follower
            ]
            return {"tweets": tweets_result} | RESULT_TRUE
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=e.args[0]
            )

    @app.get("/api/users/me")
    async def get_info_about_yourself(
        auth: Annotated[dict, Depends(check_authentication_key)],
        db: Session = Depends(get_db),
    ) -> Dict:
        """Get information about yourself"""
        user_id = auth.get("user_id")
        try:
            query = (
                select(User)
                .options(joinedload(User.followers), joinedload(User.following))
                .where(User.id == user_id)
            )
            user = db.scalar(query)
            return {"user": jsonable_encoder(user)} | RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Not found"
            )

    @app.get("/api/users/{user_id}")
    async def get_info_by_id(
        user_id: int,
        auth: Annotated[dict, Depends(check_authentication_key)],
        db: Session = Depends(get_db),
    ):
        """Get information anouther user by user id"""
        try:
            query = (
                select(User)
                .options(joinedload(User.followers), joinedload(User.following))
                .where(User.id == user_id)
            )
            user = db.scalar(query)
            return {"user": user} | RESULT_TRUE
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
