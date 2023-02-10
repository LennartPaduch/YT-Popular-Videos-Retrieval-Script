CREATE TABLE yt_channel(
    title text,
    last_updated timestamp,
    id varchar(30) PRIMARY KEY,
    trending_cnt integer,
    category_ids integer[],
    trended_countries varchar(2)[],
    CONSTRAINT uc_yt_channel_id_last_updated UNIQUE (id, last_updated)
)