import http.client
import json
import urllib.parse
import logging

# Logging ayarları
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_instagram_data(username, endpoint, pagination_token=None):
    conn = http.client.HTTPSConnection("instagram-scraper-api2.p.rapidapi.com")
    headers = {
        'X-RapidAPI-Key': "9cf1b4a59emsh2f1920dd6f80a7ap1c60abjsn20a97356e1d4",
        'X-RapidAPI-Host': "instagram-scraper-api2.p.rapidapi.com"
    }
    
    if pagination_token:
        endpoint += f"&pagination_token={urllib.parse.quote(pagination_token)}"
    
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def get_caption(item):
    caption = item.get("caption")
    if isinstance(caption, dict):
        return caption.get("text", "")
    elif isinstance(caption, str):
        return caption
    else:
        return ""

def process_user_data(data):
    if "data" not in data:
        return {"error": "Kullanıcı verisi bulunamadı"}

    user_data = data["data"]
    processed_data = {
        "username": user_data.get("username", ""),
        "full_name": user_data.get("full_name", ""),
        "follower_count": user_data.get("follower_count", 0),
        "following_count": user_data.get("following_count", 0),
        "biography": user_data.get("biography", ""),
        "external_url": user_data.get("external_url", ""),
        "is_private": user_data.get("is_private", False),
        "is_verified": user_data.get("is_verified", False),
        "profile_pic_url": user_data.get("profile_pic_url", ""),
        "media_count": user_data.get("media_count", 0),
    }
    return processed_data

def process_posts_data(data):
    if "data" not in data:
        return {"error": "Gönderi verisi bulunamadı"}

    processed_posts = []
    
    for item in data["data"].get("items", []):
        processed_item = {
            "id": item.get("id", ""),
            "caption": get_caption(item),
            "like_count": item.get("like_count", 0),
            "comment_count": item.get("comment_count", 0),
            "media_type": item.get("media_type", 0),
            "thumbnail_url": item.get("thumbnail_url", ""),
            "taken_at": item.get("taken_at", ""),
        }
        processed_posts.append(processed_item)
    
    return processed_posts

def get_all_posts(username):
    posts_endpoint = f"/v1.2/posts?username_or_id_or_url={username}"
    all_posts = []
    pagination_token = None
    
    while True:
        posts_data = get_instagram_data(username, posts_endpoint, pagination_token)
        processed_posts = process_posts_data(posts_data)
        
        if isinstance(processed_posts, dict) and "error" in processed_posts:
            logger.error(f"Hata: {processed_posts['error']}")
            break
        
        all_posts.extend(processed_posts)
        logger.info(f"Toplam gönderi sayısı: {len(all_posts)}")
        
        pagination_token = posts_data.get("pagination_token")
        if not pagination_token:
            break
    
    return all_posts  # Tüm postları döndür

def get_highlighted_stories(username):
    highlight_endpoint = f"/v1/highlights?username_or_id_or_url={username}"
    highlight_data = get_instagram_data(username, highlight_endpoint)
    
    highlighted_stories = []
    for item in highlight_data["data"]["items"]:
        simplified_item = {
            "title": item["title"],
            "cover_image_url": item["cover_media"]["cropped_image_version"]["url"]
        }
        highlighted_stories.append(simplified_item)
    
    return highlighted_stories

def get_user_info(username):
    user_endpoint = f"/v1/user/info?username_or_id_or_url={username}"
    user_data = get_instagram_data(username, user_endpoint)
    return process_user_data(user_data)

def get_limited_posts(username, limit=12):
    posts_endpoint = f"/v1.2/posts?username_or_id_or_url={username}"
    limited_posts = []
    pagination_token = None
    
    while len(limited_posts) < limit:
        posts_data = get_instagram_data(username, posts_endpoint, pagination_token)
        processed_posts = process_posts_data(posts_data)
        
        if isinstance(processed_posts, dict) and "error" in processed_posts:
            logger.error(f"Hata: {processed_posts['error']}")
            break
        
        limited_posts.extend(processed_posts[:limit - len(limited_posts)])
        logger.info(f"Toplam gönderi sayısı: {len(limited_posts)}")
        
        if len(processed_posts) < 12:  # Eğer bir sayfada 12'den az post varsa, bu son sayfadır
            break
        
        pagination_token = posts_data.get("pagination_token")
        if not pagination_token:
            break
    
    return limited_posts

def get_instagram_data_for_user(username, analysis_type='simple'):
    user_info = get_user_info(username)
    
    if user_info.get("is_private", False):
        logger.info(f"Kullanıcı {username} gizli bir hesaba sahip. Sadece temel bilgiler döndürülüyor.")
        return {
            "user_info": user_info,
            "user_feed": [],
            "stories": {"Highlighted Stories": []}
        }
    
    if analysis_type == 'simple':
        user_feed = get_limited_posts(username, 12)
    else:
        user_feed = get_limited_posts(username, 96)  # Detaylı analiz için 96 post çekiyoruz
    
    stories = {"Highlighted Stories": get_highlighted_stories(username)}
    
    return {
        "user_info": user_info,
        "user_feed": user_feed,
        "stories": stories
    }

# Main bloğunu kaldırdık çünkü bu bir modül olarak kullanılacak
