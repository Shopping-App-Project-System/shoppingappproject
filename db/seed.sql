-- ============================================================================
--  測試用種子資料（本機開發用，請勿套用在正式資料庫）
-- ----------------------------------------------------------------------------
--  用途：建完 schema 後灌入少量資料，讓首頁／商品頁／後台有東西可看。
--
--  使用方式：
--      mysql -u root -p shoppingapp < db/seed.sql
--
--  注意：測試帳號的密碼是明文（與目前程式的驗證方式一致），
--        僅供本機測試，切勿用於正式環境。
-- ============================================================================

USE `shoppingapp`;

-- ── 測試會員 ────────────────────────────────────────────────
-- 帳號 test / 密碼 test1234 / 信箱 test@example.com（已通過信箱驗證）
INSERT INTO `user` (`user_account`, `user_password`, `user_email`, `minecraft_name`, `verify_status`)
VALUES ('test', 'test1234', 'test@example.com', 'Steve', 1)
ON DUPLICATE KEY UPDATE `user_account` = `user_account`;

-- ── 測試商品 ────────────────────────────────────────────────
INSERT INTO `products`
    (`mc_item_id`, `name`, `original_price`, `sale_price`, `description`, `category`, `is_active`, `is_deleted`)
VALUES
    ('minecraft:diamond',        '鑽石',     100, 80,   '亮晶晶的鑽石，合成高階裝備必備。', '礦物與素材', 1, 0),
    ('minecraft:emerald',        '翡翠',      90, NULL, '與村民交易的通用貨幣。',           '礦物與素材', 1, 0),
    ('minecraft:iron_ingot',     '鐵錠',      30, NULL, '最泛用的基礎金屬材料。',           '礦物與素材', 1, 0),
    ('minecraft:netherite_ingot','下界合金錠', 500, 450, '目前遊戲內最堅固的材料。',         '礦物與素材', 1, 0),
    ('minecraft:oak_log',        '橡木原木',   10, NULL, '最常見的建築與合成材料。',         '木材',       1, 0)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- ── 對應庫存 ────────────────────────────────────────────────
-- 依 mc_item_id 找回剛才建立的商品 id，避免寫死流水號
INSERT INTO `product_stock` (`product_id`, `product_quantity`)
SELECT `id`,
       CASE `mc_item_id`
           WHEN 'minecraft:diamond'         THEN 50
           WHEN 'minecraft:emerald'         THEN 40
           WHEN 'minecraft:iron_ingot'      THEN 200
           WHEN 'minecraft:netherite_ingot' THEN 5
           ELSE 500
       END
FROM `products`
WHERE `mc_item_id` IN (
    'minecraft:diamond', 'minecraft:emerald', 'minecraft:iron_ingot',
    'minecraft:netherite_ingot', 'minecraft:oak_log'
)
ON DUPLICATE KEY UPDATE `product_quantity` = VALUES(`product_quantity`);

SELECT '種子資料匯入完成' AS result,
       (SELECT COUNT(*) FROM `user`)     AS users,
       (SELECT COUNT(*) FROM `products`) AS products;
