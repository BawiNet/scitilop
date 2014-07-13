CREATE TABLE `area_info` (
	`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
	`sig_lvl` CHAR(1) NOT NULL DEFAULT '0',
	`sig_cd` VARCHAR(50) NOT NULL DEFAULT '0',
	`sig_nm` VARCHAR(100) NOT NULL DEFAULT '0',
	`valid_from` DATE NOT NULL,
	`valid_to` DATE NOT NULL,
	`coord_sys` VARCHAR(100) NOT NULL,
	`geoJSON` LONGTEXT NOT NULL,
	`prev_id` INT(11) NULL DEFAULT NULL,
	`next_id` INT(11) NULL DEFAULT NULL,
	`parent_id` INT(11) NULL DEFAULT NULL,
	PRIMARY KEY (`id`),
	INDEX `prev_id` (`prev_id`),
	INDEX `next_id` (`next_id`),
	INDEX `parent_id` (`parent_id`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
AUTO_INCREMENT=60;
