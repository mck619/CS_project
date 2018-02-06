CREATE TABLE series(
    series_ID INT PRIMARY KEY NOT NULL,
    map_pool_id INT REFERENCES map_pool(map_pool_id),
    series_date DATE NOT NULL,
    demo_url VARCHAR(250),
);

CREATE TABLE team(
    team_ID INT PRIMARY KEY NOT NULL,
    team_name VARCHAR(250) NOT NULL,
);

CREATE TABLE player(
    player_id INT PRIMARY KEY NOT NULL,
    player_alias VARCHAR(250) NOT NULL,
    player_name VARCHAR(250),
);


