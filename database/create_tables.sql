CREATE TABLE series(
    series_ID INT PRIMARY KEY NOT NULL,
    map_pool_id INT REFERENCES map_pool(map_pool_id),
    series_date DATE NOT NULL,
    demo_url VARCHAR(250),
);
    
CREATE TABLE vetos(
    series_ID INT REFERENCES series(series_ID),
    veto_num INT NOT NULL,
    veto_string VARCHAR(250),
);

CREATE TABLE maps(
    map_id INT PRIMARY KEY NOT NULL,
    map_name VARCHAR(250) NOT NULL,
);

CREATE TABLE map_pool(
    map_pool_id INT PRIMARY KEY NOT NULL,
);

CREATE TABLE map_pool_maps(
    map_pool_id INT REFERENCES map_pool(map_pool_id),
    map_id INT REFERENCES maps(map_id)
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

CREATE TABLE player_team(
    player_id INT REFERENCES
);



