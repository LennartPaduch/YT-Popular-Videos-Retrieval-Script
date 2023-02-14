CREATE TABLE yt_videos_history(
    id serial PRIMARY KEY,
    video_id varchar(11) REFERENCES yt_videos (video_id),
    like_count integer,
    view_count integer,
    comment_count integer,
    timestamp timestamp,
    title varchar(256),
    thumbnail_hash varchar(64),
    thumbnail_iteration integer,
    embeddable boolean,
    caption boolean,
    blocked_regions varchar(2)[],
    trending_regions varchar(2)[],
    idx integer,
    CONSTRAINT uc_yt_videos_history_video_id_timestamp UNIQUE (video_id, timestamp)
);