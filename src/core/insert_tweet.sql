insert into `[el]#moca_prefix#tweets` (
  tweet_id, user_id, text, created_at, source
)
select %s, %s, %s, %s, %s
where not exists (select 1 from `[el]#moca_prefix#tweets` where tweet_id = %s);