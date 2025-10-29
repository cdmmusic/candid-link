-- ============================================================
-- 글로벌 플랫폼 코드 정규화 스크립트
-- 목적: 긴 플랫폼 코드를 짧은 표준 코드로 통일
-- ============================================================

-- 작업 전 통계
SELECT '===== 작업 전 통계 =====' as status;

SELECT
    platform_code,
    platform_name,
    COUNT(*) as count
FROM album_platform_links
WHERE platform_type = 'global'
GROUP BY platform_code, platform_name
ORDER BY platform_name, platform_code;

-- ============================================================
-- 플랫폼 코드 정규화
-- ============================================================

SELECT '===== Spotify: spotify → spo =====' as status;
UPDATE album_platform_links
SET platform_code = 'spo'
WHERE platform_code = 'spotify' AND platform_type = 'global';

SELECT '===== Amazon Music: amazon → ama =====' as status;
UPDATE album_platform_links
SET platform_code = 'ama'
WHERE platform_code = 'amazon' AND platform_type = 'global';

SELECT '===== Deezer: deezer → dee =====' as status;
UPDATE album_platform_links
SET platform_code = 'dee'
WHERE platform_code = 'deezer' AND platform_type = 'global';

SELECT '===== Anghami: anghami → ang =====' as status;
UPDATE album_platform_links
SET platform_code = 'ang'
WHERE platform_code = 'anghami' AND platform_type = 'global';

SELECT '===== Pandora: pandora → pdx =====' as status;
UPDATE album_platform_links
SET platform_code = 'pdx'
WHERE platform_code = 'pandora' AND platform_type = 'global';

SELECT '===== YouTube: youtube → yat =====' as status;
UPDATE album_platform_links
SET platform_code = 'yat'
WHERE platform_code = 'youtube' AND platform_type = 'global';

SELECT '===== LINE Music: line → lmj =====' as status;
UPDATE album_platform_links
SET platform_code = 'lmj'
WHERE platform_code = 'line' AND platform_type = 'global';

SELECT '===== Tidal: tidal → asp =====' as status;
UPDATE album_platform_links
SET platform_code = 'asp'
WHERE platform_code = 'tidal' AND platform_type = 'global';

SELECT '===== AWA: awm → awa =====' as status;
UPDATE album_platform_links
SET platform_code = 'awa'
WHERE platform_code = 'awm' AND platform_type = 'global';

SELECT '===== KKBox: kkbox → kkb =====' as status;
UPDATE album_platform_links
SET platform_code = 'kkb'
WHERE platform_code = 'kkbox' AND platform_type = 'global';

SELECT '===== Moov: moov → mov =====' as status;
UPDATE album_platform_links
SET platform_code = 'mov'
WHERE platform_code = 'moov' AND platform_type = 'global';

-- ============================================================
-- 작업 완료 통계
-- ============================================================

SELECT '===== 작업 후 통계 =====' as status;

SELECT
    platform_code,
    platform_name,
    COUNT(*) as count,
    SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found_count,
    ROUND(CAST(SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as success_rate
FROM album_platform_links
WHERE platform_type = 'global'
GROUP BY platform_code, platform_name
ORDER BY platform_name;

SELECT '===== 정규화 완료! =====' as status;
