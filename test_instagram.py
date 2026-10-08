import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")


# Step 0: Get your Instagram User ID directly via Instagram Login API
def get_ig_user_id():
    url = f"https://graph.instagram.com/v21.0/me?access_token={TOKEN}"
    res = requests.get(url).json()
    print("Me Response:", res)

    if "id" in res:
        return res["id"]

    raise Exception(f"Could not get Instagram User ID: {res}")


# 1. Fetch Comments Call
# 1. Fetch Comments Call with explicit fields
def fetch_comments(media_id):
    url = f"https://graph.instagram.com/v21.0/{media_id}/comments?fields=id,text,username&access_token={TOKEN}"
    response = requests.get(url)
    print("\n--- 1. FETCH COMMENTS ---")
    print(response.json())
    return response.json()


# 2. Reply to Comment Call
def reply_to_comment(comment_id, message):
    url = f"https://graph.instagram.com/v21.0/{comment_id}/replies"
    payload = {"message": message, "access_token": TOKEN}
    response = requests.post(url, data=payload)
    print("\n--- 2. REPLY TO COMMENT ---")
    print(response.json())
    return response.json()


# 3. Hide Comment Call
def hide_comment(comment_id, hide_status=True):
    url = f"https://graph.instagram.com/v21.0/{comment_id}"
    payload = {"hide": hide_status, "access_token": TOKEN}
    response = requests.post(url, data=payload)
    print("\n--- 3. HIDE COMMENT ---")
    print(response.json())
    return response.json()


if __name__ == "__main__":
    ig_user_id = get_ig_user_id()
    print(f"✅ Found Instagram User ID: {ig_user_id}")

    # Automatically fetch your latest media ID
    media_url = (
        f"https://graph.instagram.com/v21.0/{ig_user_id}/media?access_token={TOKEN}"
    )
    media_res = requests.get(media_url).json()
    print("Media Response:", media_res)

    if "data" in media_res and media_res["data"]:
        media_id = media_res["data"][0]["id"]
        print(f"📌 Using latest Media ID: {media_id}")

        # Run Step 1: Fetch comments
        comments_data = fetch_comments(media_id)
    else:
        print("⚠️ No media found. Post a test photo on your Instagram account first!")
        # Run Step 1: Fetch comments
        comments_data = fetch_comments(media_id)

        # Print out each comment found
        for comment in comments_data.get("data", []):
            print(f"💬 Comment ID: {comment.get('id')} | Text: {comment.get('text')}")
