# Weather Vessel CLI

## 개요
`wv` CLI는 물류 컨트롤 타워를 보완하여 자동 기상 점검, 주간 스케줄 제안, 다채널 알림을 제공합니다.

## 명령어

### `wv check --now`
요청 지점 또는 사전 정의된 항로의 최대 파고(Hs)와 풍속을 평가합니다.

```
wv check --now --lat 24.40 --lon 54.70 --hours 48
wv check --now --route MW4-AGI
```

### `wv schedule --week`
7일 롤링 스케줄을 생성하여 터미널에 표로 출력하고 `WV_OUTPUT_DIR`에 CSV/ICS 파일을 저장합니다.

```
wv schedule --week --route MW4-AGI --vessel DUNE_SAND \
  --vessel-speed 12.5 --route-distance 180 --cargo-hs-limit 2.2
```

### `wv notify`
지정된 항로의 리스크 요약을 생성하고 구성된 채널로 발송합니다. `--dry-run` 옵션으로 발송 없이 미리 확인할 수 있습니다.

```
wv notify --route MW4-AGI --dry-run
wv notify --route MW4-AGI
```

## 프로바이더 & 캐시
- 주요 어댑터: Stormglass, Open-Meteo Marine, NOAA WaveWatch III, Copernicus Marine
- 캐시 위치: `WV_CACHE_DIR` (기본 `~/.wv/cache`), TTL 30분 + 3시간 이내 스테일 폴백
- 모든 API 키는 환경 변수 또는 `.env`에서 로드됩니다.

## 자동화
- Cron: `0 6,17 * * * /usr/local/bin/wv notify --route MW4-AGI`
- Windows 작업 스케줄러: `schtasks /Create /SC DAILY /TN "WV_0600" /TR "wv notify --route MW4-AGI" /ST 06:00`

## 품질 게이트
PR 전 아래 명령을 실행하세요.
```
pytest -q
coverage run -m pytest
black --check .
isort --check-only .
flake8 .
mypy --strict src
```
