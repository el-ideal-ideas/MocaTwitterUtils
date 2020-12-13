insert into `[el]#moca_prefix#users` (
  user_id, name, screen_name, location, description, url, followers_count, friends_count,
  listed_count, favourites_count, profile_background_color, profile_background_image_url,
  profile_background_image_url_https, profile_image_url, profile_image_url_https,
  profile_banner_url, profile_link_color, profile_sidebar_border_color, profile_sidebar_fill_color,
  profile_text_color, created_at, update_at
) values (
  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now()
);