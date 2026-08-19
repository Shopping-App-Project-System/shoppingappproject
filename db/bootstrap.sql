-- ============================================================================
--  資料庫初始化：建立專用帳號與授權
-- ----------------------------------------------------------------------------
--  這支腳本需要用 root 執行一次即可。
--
--      mysql -u root -p < db/bootstrap.sql
--
--  它會建立一個只能存取 shoppingapp 資料庫的帳號，
--  避免應用程式直接使用 root 連線。
--
--  ⚠ 執行前請把下面的密碼改成你自己的，改完之後同步填進 .env 的 DB_PASSWORD。
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `shoppingapp`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 請把 'CHANGE_ME' 換成你自己的密碼
CREATE USER IF NOT EXISTS 'shoppingapp'@'localhost' IDENTIFIED BY 'CHANGE_ME';
CREATE USER IF NOT EXISTS 'shoppingapp'@'127.0.0.1' IDENTIFIED BY 'CHANGE_ME';

-- 只授權這個資料庫，不給全域權限
GRANT ALL PRIVILEGES ON `shoppingapp`.* TO 'shoppingapp'@'localhost';
GRANT ALL PRIVILEGES ON `shoppingapp`.* TO 'shoppingapp'@'127.0.0.1';

FLUSH PRIVILEGES;

SELECT '資料庫與帳號建立完成' AS result;
