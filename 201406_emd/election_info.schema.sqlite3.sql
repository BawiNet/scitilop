CREATE TABLE `candidate_info` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `election` TEXT NOT NULL,
    `elec_type` TEXT NOT NULL,
    `lvl` TEXT NOT NULL,
    `sig_cd` TEXT NOT NULL DEFAULT '0',
    `sig_id` INTEGER REFERENCES "area_info" ("id"),
    `precinct` TEXT NOT NULL,
    `name` TEXT NOT NULL,
    `party` TEXT NOT NULL
);

CREATE TABLE `election_info` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `election` TEXT NOT NULL,
    `elec_type` TEXT NOT NULL,
    `lvl` TEXT NOT NULL,
    `sig_cd` TEXT NOT NULL DEFAULT '0',
    `sig_id` INTEGER REFERENCES "area_info" ("id"),
    `precinct` TEXT NOT NULL,
    `candidate_id` INTEGER REFERENCES "candidate_info" ("id"),
    `count_type` TEXT NOT NULL,
    `count` INTEGER NOT NULL
);
