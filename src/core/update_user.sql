update `[el]#moca_prefix#users` set
  name=%s, screen_name=%s, location=%s, description=%s, url=%s, followers_count=%s,
  friends_count=%s, listed_count=%s, favourites_count=%s,
  profile_background_color=%s, profile_background_image_url=%s, profile_background_image_url_https=%s,
  profile_image_url=%s, profile_image_url_https=%s, profile_banner_url=%s, profile_link_color=%s,
  profile_sidebar_border_color=%s, profile_sidebar_fill_color=%s, profile_text_color=%s,
  update_at=now()
where
  user_id = %s;