insert into `[el]#moca_prefix#tweets` (
  tweet_id, user_id, text, created_at, source
)
select %s, %s, %s, %s, %s;