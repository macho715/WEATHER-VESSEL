# 웨더 베슬 사용 가이드

- `pip install -e .[all]` 명령으로 의존성을 설치합니다.
- `.env.example`을 참고하여 `.env`에 공급자 및 알림 환경변수를 설정합니다.
- `wv check --now --route MW4-AGI`로 즉시 위험 평가를 확인합니다.
- `wv schedule --week --route MW4-AGI` 명령으로 주간 일정표, CSV, ICS를 생성합니다.
- `wv notify --route MW4-AGI --dry-run --slack --telegram`으로 채널별 알림을 검증합니다.
- README의 예시를 활용해 Asia/Dubai 기준 06:00/17:00 자동화를 cron 또는 Windows 작업 스케줄러에 등록합니다.
