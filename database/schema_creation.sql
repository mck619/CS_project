-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema scraped_data
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema scraped_data
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `scraped_data` DEFAULT CHARACTER SET utf8 ;
USE `scraped_data` ;

-- -----------------------------------------------------
-- Table `scraped_data`.`teams`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`teams` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NULL,
  `location` VARCHAR(45) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`series`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`series` (
  `id` INT NOT NULL,
  `date` TIMESTAMP NULL,
  `url` VARCHAR(45) NULL,
  `stats_url` VARCHAR(45) NULL,
  `demo_url` VARCHAR(45) NULL,
  `winner` INT NOT NULL,
  `loser` INT NOT NULL,
  `score` VARCHAR(45) NULL,
  `season` VARCHAR(45) NULL,
  PRIMARY KEY (`id`),
  INDEX `winner` (`winner` ASC),
  INDEX `loser` (`loser` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`match`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`match` (
  `series_id` INT NOT NULL,
  `id` INT NOT NULL,
  `match_num` INT NULL,
  `score` VARCHAR(45) NULL,
  `winner` INT NULL,
  `loser` INT NULL,
  `map` VARCHAR(45) NULL,
  PRIMARY KEY (`id`),
  INDEX `match_num_idx` (`match_num` ASC),
  INDEX `winner` (`winner` ASC),
  INDEX `loser` (`loser` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`round_history`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`round_history` (
  `series_id` INT NULL,
  `id` INT NOT NULL,
  `match_id` INT NULL,
  `round_num` INT NULL,
  `match_num` INT NULL,
  `half` INT NULL,
  `ct` VARCHAR(45) NULL,
  `t` VARCHAR(45) NULL,
  `ending` VARCHAR(45) NULL,
  `side_winner` VARCHAR(45) NULL,
  `winner` VARCHAR(45) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`players`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`players` (
  `id` INT NOT NULL,
  `name` VARCHAR(45) NULL,
  `nickname` VARCHAR(45) NULL,
  `country` VARCHAR(45) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`vetos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`vetos` (
  `id` INT NOT NULL,
  `team_id` INT NULL,
  `veto_num` INT NULL,
  `map` VARCHAR(45) NULL,
  `action` VARCHAR(45) NULL,
  `series_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `series_id` (`series_id` ASC),
  INDEX `team` (`team_id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`player_match_soreboards`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`player_match_soreboards` (
  `id` INT NOT NULL,
  `player_id` INT NULL,
  `team_id` INT NULL,
  `kills` INT NULL,
  `deaths` INT NULL,
  `plus_minus` INT NULL,
  `ADR` DOUBLE NULL,
  `KAST` DOUBLE NULL,
  `rating` DOUBLE NULL,
  `match_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `team` (`team_id` ASC),
  INDEX `player` (`player_id` ASC),
  INDEX `match` (`match_id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`team_match_stats`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`team_match_stats` (
  `id` INT NOT NULL,
  `match_id` INT NULL,
  `kills` INT NULL,
  `assists` INT NULL,
  `deaths` INT NULL,
  `team_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `team` (`team_id` ASC),
  INDEX `match` (`match_id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `scraped_data`.`player_match_total_kills`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`player_match_total_kills` (
  `id` INT NOT NULL,
  `killer_id` INT NULL,
  `killed_id` INT NULL,
  `count` INT NULL,
  `match_id` INT NULL,
  `killer_team_id` INT NULL,
  `killed_team_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `killed` (`killed_id` ASC),
  INDEX `killer` (`killer_id` ASC),
  INDEX `match_id` (`match_id` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = big5;


-- -----------------------------------------------------
-- Table `scraped_data`.`player_match_awp_kills`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`player_match_awp_kills` (
  `id` INT NOT NULL,
  `killer_id` INT NULL,
  `killed_id` INT NULL,
  `count` INT NULL,
  `match_id` INT NULL,
  `killer_team_id` INT NULL,
  `killed_team_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `killed` (`killed_id` ASC),
  INDEX `killer` (`killer_id` ASC),
  INDEX `match_id` (`match_id` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = big5;


-- -----------------------------------------------------
-- Table `scraped_data`.`player_match_first_kills`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`player_match_first_kills` (
  `id` INT NOT NULL,
  `killer_id` INT NULL,
  `killed_id` INT NULL,
  `count` INT NULL,
  `match_id` INT NULL,
  `killer_team_id` INT NULL,
  `killed_team_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `killed` (`killed_id` ASC),
  INDEX `killer` (`killer_id` ASC),
  INDEX `match_id` (`match_id` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = big5;


-- -----------------------------------------------------
-- Table `scraped_data`.`scraper_errors`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scraped_data`.`scraper_errors` (
  `id` INT NOT NULL,
  `time` DATETIME NULL,
  `logger_name` VARCHAR(45) NULL,
  `exception_type` VARCHAR(45) NULL,
  `url` VARCHAR(45) NULL,
  `exception_message` VARCHAR(45) NULL,
  `traceback` VARCHAR(45) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
