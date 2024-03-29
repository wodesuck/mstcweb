CREATE TABLE pages (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    title VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    layout VARCHAR(64) NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT 0,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE (name)
) DEFAULT CHARSET=utf8;

CREATE TABLE `events` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(64) NOT NULL,
    `content_fields` VARCHAR(4096) NOT NULL,
    `start_time` TIMESTAMP NOT NULL DEFAULT 0,
    `end_time` TIMESTAMP NOT NULL DEFAULT 0,
    `created_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;
CREATE UNIQUE INDEX `name` ON `events` (`name`);

CREATE TABLE `forms_data` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `event_id` INTEGER NOT NULL,
    `name` VARCHAR(128) NOT NULL,
    `email` VARCHAR(128) NOT NULL,
    `content` TEXT NOT NULL,
    `status` TINYINT NOT NULL DEFAULT 0,
    `created_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;
CREATE INDEX `event_id` ON `forms_data` (`event_id`);

CREATE TABLE `users` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(32) NOT NULL,
    `pwhash` VARCHAR(60) NOT NULL,
    `salt` VARCHAR(29) NOT NULL,
    `token` VARCHAR(32) DEFAULT NULL,
    `client_feature` VARCHAR(32) DEFAULT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;
CREATE UNIQUE INDEX `username` ON `users` (`username`);
