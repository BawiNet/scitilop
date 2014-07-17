CREATE TABLE `area_info` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `sig_lvl` TEXT NOT NULL DEFAULT '0',
    `sig_cd` TEXT NOT NULL DEFAULT '0',
    `sig_nm` TEXT NOT NULL DEFAULT '0',
    `prev_id` INTEGER NULL DEFAULT NULL,
    `next_id` INTEGER NULL DEFAULT NULL,
    `parent_id` INTEGER NULL DEFAULT NULL
);
CREATE INDEX `next_id` ON `area_info` (`next_id`);
CREATE INDEX `parent_id` ON `area_info` (`parent_id`);
CREATE INDEX `prev_id` ON `area_info` (`prev_id`);

