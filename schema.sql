 CREATE TABLE messages
  (
     id            INTEGER PRIMARY KEY auto_increment,
     insert_time   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     token         VARCHAR(43) NOT NULL,
     time_received TIMESTAMP NOT NULL,
     sender        VARCHAR(20) NOT NULL,
     receiver      VARCHAR(20) NOT NULL,
     message       TEXT
  )
CHARACTER SET utf8mb4;

CREATE TABLE registration
  (
     last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     token        VARCHAR(43) NOT NULL,
     discord_id   BIGINT(20) UNIQUE,
     discord_name VARCHAR(32),
     is_verified  BOOLEAN DEFAULT NULL,
     callsign     VARCHAR(20) DEFAULT NULL,
     PRIMARY KEY(token, discord_id)
  )
CHARACTER SET utf8mb4;  

CREATE TABLE stats
   (
      id                INTEGER PRIMARY KEY AUTO_INCREMENT,
      tsRegistered      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      tsDeregistered    TIMESTAMP NULL DEFAULT NULL,
      intMsgCount       INTEGER DEFAULT '0',
      intSUPMsgCount    INTEGER DEFAULT '0',
      intAutoATCCount   INTEGER DEFAULT '0',
      token             VARCHAR(43) DEFAULT NULL
   )
CHARACTER SET utf8mb4;