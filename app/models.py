from typing import Any, Dict, List

from sqlalchemy import Column, ForeignKey, Integer, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

likes_table = Table(
    "likes",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id"),
        primary_key=True,
    ),
    Column("tweet_id", Integer, ForeignKey("tweets.id"), primary_key=True),
    UniqueConstraint("user_id", "tweet_id", name="unique_likes"),
)

user_following = Table(
    "user_following",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("follower_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    following = relationship(
        "User",
        lambda: user_following,
        primaryjoin=lambda: User.id == user_following.c.follower_id,
        secondaryjoin=lambda: User.id == user_following.c.user_id,
        back_populates="followers",
    )

    followers = relationship(
        "User",
        lambda: user_following,
        primaryjoin=lambda: User.id == user_following.c.user_id,
        secondaryjoin=lambda: User.id == user_following.c.follower_id,
        back_populates="following",
    )

    tweets = relationship(
        "Tweet",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(Base):
    __tablename__ = "medias"
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(nullable=False)
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id"), nullable=True
    )
    tweet = relationship("Tweet", back_populates="attachments")


class Tweet(Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(nullable=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    attachments: Mapped[List[Media]] = relationship(
        "Media",
        back_populates="tweet",
        cascade="all, delete-orphan",
    )
    likes: Mapped[List[User]] = relationship(secondary=likes_table)
    author = relationship("User", back_populates="tweets", lazy="joined")

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Key(Base):
    __tablename__ = "keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key: Mapped[str] = mapped_column(nullable=False)

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
