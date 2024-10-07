from io import BytesIO

from pytest_schema import schema

from .conftest import FAKE_USER, TEST_USER, client
from .pytest_schemas import error_shema, tweet_schema, user_schema


def test_authentication_by_wrong_key():
    response = client.get("/api/users/me", headers={"Api-Key": "wrong_key"})
    result = response.json()
    assert response.status_code == 401
    assert result.get("error_message") == "Invalid API Key"


def test_upload_media():
    user_key = TEST_USER["api_key"]
    image_content = b"test image"
    image_file = BytesIO(image_content)
    files = {"file": ("image.jpg", image_file, "image/jpeg")}
    response = client.post(
        "/api/medias", files=files, headers={"Api-Key": user_key}
    )
    assert response.status_code == 200
    result = response.json()
    assert result == {"media_id": 1, "result": True}


def test_add_tweet():
    user_key = TEST_USER["api_key"]
    tweet_data = {"tweet_data": "new tweet", "tweet_media_ids": [1]}
    response = client.post(
        "/api/tweets", json=tweet_data, headers={"Api-Key": user_key}
    )
    assert response.status_code == 200
    result = response.json()
    assert result == {"tweet_id": 1, "result": True}


def test_add_like():
    user_key_1 = TEST_USER["api_key"]
    user_key_2 = FAKE_USER["api_key"]
    tweet_id = 1
    response_1 = client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"Api-Key": user_key_1}
    )
    result_1 = response_1.json()
    assert result_1.get("result") is True
    response_2 = client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"Api-Key": user_key_2}
    )
    result_2 = response_2.json()
    assert result_2.get("result") is True


def test_delete_like():
    user_key = TEST_USER["api_key"]
    tweet_id = 1
    response_delete = client.delete(
        f"/api/tweets/{tweet_id}/likes", headers={"Api-Key": user_key}
    )
    result = response_delete.json()
    assert response_delete.status_code == 200
    assert result.get("result") is True


def test_follow_user():
    user_key_1 = TEST_USER["api_key"]
    user_key_2 = FAKE_USER["api_key"]
    response_1 = client.post(
        "/api/users/2/follow", headers={"Api-Key": user_key_1}
    )
    result_1 = response_1.json()
    assert response_1.status_code == 200
    assert result_1.get("result") is True
    response_2 = client.post(
        "/api/users/1/follow", headers={"Api-Key": user_key_2}
    )
    result_2 = response_2.json()
    assert response_2.status_code == 200
    assert result_2.get("result") is True


def test_get_info_about_yourself():
    user_key = TEST_USER["api_key"]
    username = TEST_USER["username"]
    response = client.get("/api/users/me", headers={"Api-Key": user_key})
    assert response.status_code == 200
    result_data = response.json()
    assert result_data.get("user").get("name") == username
    assert schema(user_schema) == result_data


def test_get_info_user():
    username = FAKE_USER["username"]
    user_id = 2
    user_key = TEST_USER["api_key"]
    response = client.get(
        f"/api/users/{user_id}", headers={"Api-Key": user_key}
    )
    result_data = response.json()
    assert response.status_code == 200
    assert result_data.get("user").get("name") == username
    assert result_data.get("result") is True


def test_unfollow_user():
    user_key = TEST_USER["api_key"]
    response = client.delete(
        "/api/users/2/follow", headers={"Api-Key": user_key}
    )
    result = response.json()
    assert response.status_code == 200
    assert result.get("result") is True


def test_get_tweets():
    user_key = TEST_USER["api_key"]
    response = client.get("/api/tweets", headers={"Api-Key": user_key})
    result = response.json()
    assert response.status_code == 200
    assert schema(tweet_schema) == result


def test_delete_tweet_by_wrong_user():
    user_key = FAKE_USER["api_key"]
    tweet_id = 1
    response = client.delete(
        f"/api/tweets/{tweet_id}", headers={"Api-Key": user_key}
    )
    result_data = response.json()
    assert response.status_code == 400
    assert schema(error_shema) == result_data


def test_delete_tweet():
    user_key = TEST_USER["api_key"]
    tweet_id = 1
    response = client.delete(
        f"/api/tweets/{tweet_id}", headers={"Api-Key": user_key}
    )
    result_data = response.json()
    assert response.status_code == 200
    assert result_data.get("result") is True
