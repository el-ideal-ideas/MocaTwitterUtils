create table if not exists `%stweets` (
    tweet_id bigint primary key,
    user_id bigint not null,
    text varchar(512) not null,
    created_at varchar(64) not null,
    source varchar(64) default null,
    foreign key (user_id) references `%susers` (user_id)
)engine=innodb  default charset=utf8mb4;