CREATE DATABASE IF NOT EXISTS thunder;
USE thunder;
CREATE TABLE IF NOT EXISTS user
     (fname	VARCHAR(100), 
      lname	VARCHAR(100),
      role	VARCHAR(100),
      password	VARCHAR(100),
      username	VARCHAR(100),
      PRIMARY KEY (username));
INSERT INTO user VALUES('Default', 'Admin', 'SUPERUSER', '49eff747f7b66f70133bfe00aa8ac2d6b0fbee5be80e52537b0163f147d20418', 'admin');
