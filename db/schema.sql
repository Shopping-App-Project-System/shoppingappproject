-- ============================================================================
--  MineMarket 資料庫結構
-- ----------------------------------------------------------------------------
--  本檔案由 models/ 內既有的 SQL 語句逆向整理而成（原專案沒有保留建表腳本）。
--  欄位型別依實際用途推定，若與正式環境有出入，以正式環境為準。
--
--  使用方式：
--      mysql -u root -p < db/schema.sql
--
--  字元集一律使用 utf8mb4：商品名稱、分類、訂單狀態皆為中文，
--  且需支援 emoji（utf8mb3 會在 4 byte 字元上失敗）。
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `shoppingapp`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `shoppingapp`;


-- ─────────────────────────────────────────────────────────────
--  user：會員帳號
--  同時承載三種狀態：帳號基本資料、信箱驗證流程、登入 session
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `user` (
    `id`                 INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    `user_account`       VARCHAR(50)     NOT NULL                COMMENT '登入帳號',
    -- 長度預留 255：目前存明文，改為 bcrypt/argon2 雜湊後不需再 ALTER
    `user_password`      VARCHAR(255)    NOT NULL                COMMENT '密碼',
    `user_email`         VARCHAR(255)    NOT NULL                COMMENT '電子信箱',
    `minecraft_name`     VARCHAR(32)     DEFAULT NULL            COMMENT '綁定的 Minecraft 角色名，發貨用',
    `pic_path`           VARCHAR(500)    DEFAULT NULL            COMMENT '大頭貼網址（Cloudinary）',

    -- 信箱驗證 / 忘記密碼流程
    `token`              VARCHAR(64)     DEFAULT NULL            COMMENT '驗證用一次性 token',
    `code`               VARCHAR(10)     DEFAULT NULL            COMMENT '信箱驗證碼',
    `code_expires_at`    DATETIME        DEFAULT NULL            COMMENT '驗證碼到期時間',
    `verify_status`      TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '信箱是否已驗證',

    -- 單裝置登入控制（同一帳號同時只能有一個有效 session）
    `session_token`      VARCHAR(64)     DEFAULT NULL            COMMENT '目前有效的 session token',
    `session_expires_at` DATETIME        DEFAULT NULL            COMMENT 'session 到期時間',

    `created_at`         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_account` (`user_account`),
    UNIQUE KEY `uq_user_email`   (`user_email`),
    KEY `idx_user_token`         (`token`),
    KEY `idx_user_session_token` (`session_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='會員';


-- ─────────────────────────────────────────────────────────────
--  products：商品主檔
--  is_active  = 上架 / 下架（使用者看得到與否）
--  is_deleted = 軟刪除（後台列表看得到與否），兩者互相獨立
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `products` (
    `id`             INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    `mc_item_id`     VARCHAR(100)   NOT NULL             COMMENT 'Minecraft item id，如 minecraft:diamond',
    `name`           VARCHAR(100)   NOT NULL             COMMENT '商品名稱',
    `original_price` INT            NOT NULL DEFAULT 0   COMMENT '原價',
    `sale_price`     INT            DEFAULT NULL         COMMENT '特價；NULL 表示不特價',
    `description`    TEXT                                COMMENT '商品描述',
    `product_pic`    VARCHAR(500)   DEFAULT NULL         COMMENT '商品主圖網址（Cloudinary）',
    `category`       VARCHAR(50)    DEFAULT NULL         COMMENT '分類，對應 data/mc_items.py 的分類名',
    `tag`            VARCHAR(50)    DEFAULT NULL         COMMENT '標籤（熱銷／新品等）',
    `is_active`      TINYINT(1)     NOT NULL DEFAULT 1   COMMENT '1=上架 0=下架',
    `is_deleted`     TINYINT(1)     NOT NULL DEFAULT 0   COMMENT '1=已軟刪除',
    `created_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_products_active`   (`is_active`, `is_deleted`),
    KEY `idx_products_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品';


-- ─────────────────────────────────────────────────────────────
--  product_stock：庫存（與商品 1 對 1）
--  獨立成表是為了讓扣庫存能單獨鎖列，不影響商品資料讀取
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `product_stock` (
    `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `product_id`       INT UNSIGNED NOT NULL,
    `product_quantity` INT          NOT NULL DEFAULT 0 COMMENT '剩餘庫存',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_stock_product` (`product_id`),
    CONSTRAINT `fk_stock_product` FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品庫存';


-- ─────────────────────────────────────────────────────────────
--  product_pics：商品附圖（與商品 1 對多）
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `product_pics` (
    `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `product_id`  INT UNSIGNED NOT NULL,
    `product_pic` VARCHAR(500) NOT NULL COMMENT '附圖網址',

    PRIMARY KEY (`id`),
    KEY `idx_pics_product` (`product_id`),
    CONSTRAINT `fk_pics_product` FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品附圖';


-- ─────────────────────────────────────────────────────────────
--  cart_items：購物車
--  upsert_cart() 使用 ON DUPLICATE KEY UPDATE，
--  因此 (user_id, product_id) 必須有 UNIQUE 索引，否則會重複新增。
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `cart_items` (
    `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id`    INT UNSIGNED NOT NULL,
    `product_id` INT UNSIGNED NOT NULL,
    `quantity`   INT          NOT NULL DEFAULT 1,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_cart_user_product` (`user_id`, `product_id`),
    KEY `idx_cart_product` (`product_id`),
    CONSTRAINT `fk_cart_user` FOREIGN KEY (`user_id`)
        REFERENCES `user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cart_product` FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='購物車';


-- ─────────────────────────────────────────────────────────────
--  orders：訂單
--  status 目前使用的值：已完成／待付款／付款失敗／已取消
--  所有營收報表都以 status = '已完成' 過濾。
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `orders` (
    `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id`         INT UNSIGNED NOT NULL,
    `total`           INT          NOT NULL DEFAULT 0 COMMENT '訂單總金額',
    `payment_method`  VARCHAR(50)  DEFAULT NULL       COMMENT '付款方式',
    `note`            VARCHAR(500) DEFAULT NULL       COMMENT '訂單備註',
    `status`          VARCHAR(20)  NOT NULL DEFAULT '已完成',
    `ecpay_trade_no`  VARCHAR(20)  DEFAULT NULL       COMMENT '綠界 MerchantTradeNo（上限 20 字元）',
    `ecpay_rtn_code`  VARCHAR(10)  DEFAULT NULL       COMMENT '綠界回傳代碼，1 為成功',
    `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_orders_ecpay_trade_no` (`ecpay_trade_no`),
    KEY `idx_orders_user`    (`user_id`),
    KEY `idx_orders_status`  (`status`),
    KEY `idx_orders_created` (`created_at`),
    CONSTRAINT `fk_orders_user` FOREIGN KEY (`user_id`)
        REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='訂單';


-- ─────────────────────────────────────────────────────────────
--  order_items：訂單明細
--  price 記錄「下單當下」的售價，商品日後改價不影響歷史訂單。
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `order_items` (
    `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`   INT UNSIGNED NOT NULL,
    `product_id` INT UNSIGNED NOT NULL,
    `quantity`   INT          NOT NULL DEFAULT 1,
    `price`      INT          NOT NULL DEFAULT 0 COMMENT '成交單價（下單當下）',

    PRIMARY KEY (`id`),
    KEY `idx_items_order`   (`order_id`),
    KEY `idx_items_product` (`product_id`),
    CONSTRAINT `fk_items_order` FOREIGN KEY (`order_id`)
        REFERENCES `orders` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_items_product` FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='訂單明細';


-- ─────────────────────────────────────────────────────────────
--  pending_deliveries：待發道具佇列
--  玩家下單時若不在線上，道具無法立即 /give，先排進此表，
--  等玩家上線再補發（見 mc_bridge.py）。
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `pending_deliveries` (
    `id`           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_account` VARCHAR(50)  NOT NULL,
    `mc_item_id`   VARCHAR(100) NOT NULL COMMENT 'Minecraft item id',
    `quantity`     INT          NOT NULL DEFAULT 1,
    `order_id`     INT UNSIGNED DEFAULT NULL,
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_pending_user`  (`user_account`),
    KEY `idx_pending_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='待發道具佇列';


-- ─────────────────────────────────────────────────────────────
--  manage_log：後台操作日誌
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `manage_log` (
    `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `admin_account` VARCHAR(50)  NOT NULL COMMENT '操作者帳號',
    `action`        VARCHAR(50)  NOT NULL COMMENT '動作，如 新增／下架／刪除',
    `product_id`    INT UNSIGNED DEFAULT NULL,
    `product_name`  VARCHAR(100) DEFAULT NULL COMMENT '冗餘保存，商品刪除後日誌仍可讀',
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_log_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='後台操作日誌';


-- ─────────────────────────────────────────────────────────────
--  註：settings.py 另有宣告 BRANCH_C_ACTIVE_TAG_TABLE = "active_tag"，
--      但全專案沒有任何程式碼使用它，故此處不建立該表。
--      若確定不再需要，建議連同該設定一併移除。
-- ─────────────────────────────────────────────────────────────
