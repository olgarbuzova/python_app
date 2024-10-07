tweet_schema = {
    "tweets": [
        {
            "id": int,
            "content": str,
            "attachments": [str],
            "author": {"id": int, "name": str},
            "likes": [{"user_id": int, "name": str}],
        },
    ],
    "result": True,
}

user_schema = {
    "user": {
        "id": int,
        "name": str,
        "followers": [{"id": int, "name": str}],
        "following": [{"id": int, "name": str}],
    },
    "result": True,
}

error_shema = {"result": False, "error_type": str, "error_message": str}
