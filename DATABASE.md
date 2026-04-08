# Rivals 2 Elo Backend Database Schema

## Overview
This document describes the database schema for the Rivals 2 Elo tracking system. The database stores information about matches, characters, stages, moves, seasons, and tiers for the Rivals 2 fighting game.

## Tables

### Characters
Stores information about playable characters in Rivals 2.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | int(11) | PK, Auto Increment | Unique identifier for the character |
| character_name | varchar(45) | NOT NULL | Internal name of the character |
| display_name | varchar(45) | NOT NULL | Display name shown to users |
| release_date | date | NOT NULL | Date the character was released |
| list_order | int(3) | DEFAULT NULL | Order for displaying characters in lists |

### Moves
Stores information about all move types in the game.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | int(11) | PK, Auto Increment | Unique identifier for the move |
| display_name | varchar(45) | NOT NULL, UNIQUE | Full name of the move |
| short_name | varchar(45) | NOT NULL, UNIQUE | Abbreviated name of the move |
| list_order | int(3) | DEFAULT NULL | Order for displaying moves in lists |
| category | varchar(45) | DEFAULT NULL | Category or type of the move |

### Stages
Stores information about game stages/maps.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | int(11) | PK, Auto Increment | Unique identifier for the stage |
| stage_name | varchar(45) | NOT NULL, UNIQUE | Internal name of the stage |
| display_name | varchar(45) | NOT NULL, UNIQUE | Display name shown to users |
| counter_pick | int(11) | NOT NULL, DEFAULT 1 | Whether the stage is a counter-pick stage |
| list_order | int(3) | DEFAULT NULL | Order for displaying stages in lists |
| stage_type | varchar(45) | DEFAULT NULL | Type of stage (e.g., starter, counter-pick) |
| active | tinyint(4) | DEFAULT 1 | Whether the stage is currently active/available |
| ranked_singles | tinyint(4) | DEFAULT 1 | Whether the stage is available in ranked singles |
| casual_singles | tinyint(4) | DEFAULT 1 | Whether the stage is available in casual singles |
| ranked_doubles | tinyint(4) | DEFAULT 1 | Whether the stage is available in ranked doubles |
| casual_doubles | tinyint(4) | DEFAULT 1 | Whether the stage is available in casual doubles |
| aetherian | tinyint(4) | DEFAULT 1 | Whether the stage is available in Aetherian mode |

### Seasons
Stores information about competitive seasons.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | int(11) | PK, Auto Increment | Unique identifier for the season |
| start_date | datetime | DEFAULT NULL | Start date of the season |
| end_date | datetime | DEFAULT NULL | End date of the season |
| short_name | varchar(100) | DEFAULT NULL | Abbreviated name of the season |
| display_name | varchar(100) | DEFAULT NULL | Display name of the season |
| base_leaderboard | varchar(50) | DEFAULT NULL | Reference to base leaderboard |
| pure_leaderboard | varchar(50) | DEFAULT NULL | Reference to pure leaderboard |
| season_index | int(3) | DEFAULT NULL | Numerical index of the season |
| steam_leaderboard | varchar(45) | DEFAULT NULL | Reference to Steam leaderboard |

### Tiers
Stores information about skill tiers/rankings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | int(10) | PK, Auto Increment | Unique identifier for the tier |
| tier_display_name | varchar(45) | DEFAULT NULL | Display name of the tier (e.g., "Gold", "Platinum") |
| tier_short_name | varchar(45) | DEFAULT NULL | Abbreviated name of the tier |
| min_threshold | int(10) | DEFAULT NULL | Minimum ELO for this tier |
| max_threshold | int(10) | DEFAULT NULL | Maximum ELO for this tier |

### Matches
Stores detailed information about individual matches.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | int(11) | PK, Auto Increment | Unique identifier for the match |
| match_date | datetime | NOT NULL | Date and time when the match occurred |
| elo_rank_new | int(11) | NOT NULL, DEFAULT -1 | Player's ELO rating after the match |
| elo_rank_old | int(11) | NOT NULL, DEFAULT -1 | Player's ELO rating before the match |
| elo_change | int(11) | NOT NULL, DEFAULT 0 | Change in ELO from the match |
| match_win | tinyint(4) | NOT NULL, DEFAULT 0 | Whether the player won the match (1 for win, 0 for loss) |
| match_forfeit | int(2) | NOT NULL, DEFAULT 0 | Whether the match was a forfeit |
| ranked_game_number | int(11) | NOT NULL, DEFAULT -1 | Sequential number of ranked games played |
| total_wins | int(11) | NOT NULL, DEFAULT -1 | Total number of wins |
| win_streak_value | int(11) | NOT NULL, DEFAULT -1 | Current win streak value |
| opponent_elo | int(11) | NOT NULL, DEFAULT -1 | Opponent's ELO rating |
| opponent_estimated_elo | int(11) | NOT NULL, DEFAULT -1 | Estimated ELO of opponent |
| opponent_name | varchar(200) | NOT NULL, DEFAULT '' | Name of the opponent |
| game_1_char_pick | int(5) | NOT NULL, DEFAULT -1 | Character ID picked by player in game 1 |
| game_1_opponent_pick | int(5) | NOT NULL, DEFAULT -1 | Character ID picked by opponent in game 1 |
| game_1_stage | int(5) | NOT NULL, DEFAULT -1 | Stage ID for game 1 |
| game_1_winner | int(11) | NOT NULL, DEFAULT -1 | Winner of game 1 |
| game_1_final_move_id | int(3) | DEFAULT -1 | Final move ID used in game 1 |
| game_1_duration | int(11) | DEFAULT -1 | Duration of game 1 in seconds |
| game_2_char_pick | int(5) | NOT NULL, DEFAULT -1 | Character ID picked by player in game 2 |
| game_2_opponent_pick | int(5) | NOT NULL, DEFAULT -1 | Character ID picked by opponent in game 2 |
| game_2_stage | int(5) | NOT NULL, DEFAULT -1 | Stage ID for game 2 |
| game_2_winner | int(11) | NOT NULL, DEFAULT -1 | Winner of game 2 |
| game_2_final_move_id | int(3) | DEFAULT -1 | Final move ID used in game 2 |
| game_2_duration | int(5) | DEFAULT -1 | Duration of game 2 in seconds |
| game_3_char_pick | int(5) | NOT NULL, DEFAULT -1 | Character ID picked by player in game 3 |
| game_3_opponent_pick | int(5) | NOT NULL, DEFAULT -1 | Character ID picked by opponent in game 3 |
| game_3_stage | int(5) | NOT NULL, DEFAULT -1 | Stage ID for game 3 |
| game_3_winner | int(11) | NOT NULL, DEFAULT -1 | Winner of game 3 |
| game_3_final_move_id | int(3) | DEFAULT -1 | Final move ID used in game 3 |
| game_3_duration | int(5) | DEFAULT -1 | Duration of game 3 in seconds |
| season_id | int(5) | NOT NULL, DEFAULT -1 | Foreign key to seasons table |
| final_move_id | int(3) | DEFAULT -1 | Final move ID used in the match |
| notes | varchar(450) | DEFAULT NULL | Additional notes about the match |
| ranked_placement_match | tinyint(4) | DEFAULT 0 | Whether this is a placement match |
| ranked_postplacement_match | tinyint(4) | DEFAULT 0 | Whether this is a post-placement match |

### Indexes on Matches Table
- PRIMARY KEY (`id`, `season_id`)
- UNIQUE KEY `id_UNIQUE` (`id`)
- UNIQUE KEY `unique_game_per_season` (`season_id`, `ranked_game_number`)
- KEY `game_1_stage_fk_idx` (`game_1_stage`)
- KEY `game_2_stage_fk_idx` (`game_2_stage`)
- KEY `game_3_stage_fk_idx` (`game_3_stage`)
- KEY `game_1_char_pick_fk_idx` (`game_1_char_pick`)
- KEY `game_1_opponent_pick_fk_idx` (`game_1_opponent_pick`)
- KEY `game_2_char_pick_fk_idx` (`game_2_char_pick`)
- KEY `game_2_opponent_pick_fk_idx` (`game_2_opponent_pick`)
- KEY `game_3_char_pick_fk_idx` (`game_3_char_pick`)
- KEY `game_3_opponent_pick_fk_idx` (`game_3_opponent_pick`)
- KEY `season_id_fk_idx` (`season_id`)
- KEY `final_move_fk_idx` (`final_move_id`)
- KEY `game_2_final_move_id_fk_idx` (`game_2_final_move_id`)
- KEY `game_1_final_move_id_fk_idx` (`game_1_final_move_id`)
- KEY `game_3_final_move_id_fk_idx` (`game_3_final_move_id`)

### Foreign Key Constraints on Matches Table
- `game_1_char_pick_fk`: References `characters(id)` ON DELETE CASCADE
- `game_1_final_move_id_fk`: References `moves(id)` ON DELETE NO ACTION
- `game_1_opponent_pick_fk`: References `characters(id)` ON DELETE CASCADE
- `game_1_stage_fk`: References `stages(id)` ON DELETE CASCADE
- `game_2_char_pick_fk`: References `characters(id)` ON DELETE CASCADE
- `game_2_final_move_id_fk`: References `moves(id)` ON DELETE NO ACTION
- `game_2_opponent_pick_fk`: References `characters(id)` ON DELETE CASCADE
- `game_2_stage_fk`: References `stages(id)` ON DELETE CASCADE
- `game_3_char_pick_fk`: References `characters(id)` ON DELETE CASCADE
- `game_3_final_move_id_fk`: References `moves(id)` ON DELETE NO ACTION
- `game_3_opponent_pick_fk`: References `characters(id)` ON DELETE CASCADE
- `game_3_stage_fk`: References `stages(id)` ON DELETE CASCADE
- `season_id_fk_idx`: References `seasons(id)`
- `final_move_fk_idx`: References `moves(id)`

### Triggers
- `set_season_id_before_insert`: BEFORE INSERT trigger on matches table that automatically sets the season_id based on the match_date falling between a season's start_date and end_date. If no matching season is found, it raises an error.

### Views
- `matches_vw`: A view that joins matches with characters, stages, and moves to provide a denormalized view with display names and additional descriptive fields instead of just IDs.

## Relationships
- Matches reference Characters three times (player pick, opponent pick for each of up to 3 games)
- Matches reference Stages three times (stage for each of up to 3 games)
- Matches reference Moves up to 4 times (final move for each of up to 3 games, and overall match final move)
- Matches reference Seasons through season_id
- Matches have a composite primary key of id and season_id

## Notes
- The database uses utf8mb3 character set with utf8mb3_uca1400_ai_ci collation
- Many fields have default values of -1 to indicate unset/unapplicable values
- The matches table stores data for up to 3 games per match (best-of-3 format)
- The view matches_vw provides a more user-friendly representation of match data with joined descriptive fields