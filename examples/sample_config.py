# 데모용 설정 파일 — 실제 비밀이 아닙니다(고도화 검출 시연용).
# 개발자 프로파일에서 secret/ip 검출기가 활성화되어 아래 값들이 잡힙니다.

# DB 접속정보(URL 안에 계정/비밀번호) → "DB 접속정보"(검증됨)
DATABASE_URL = "mysql://admin:S3cretP@ssw0rd@10.20.30.40:3306/customers"

# AWS Access Key 형식(AKIA + 16) → "AWS Access Key"(검증됨)
AWS_ACCESS_KEY_ID = "AKIA1234567890ABCD12"

# 고엔트로피 토큰 → "API 키/시크릿"(검증됨)
api_key = "aZ9kQ2mB7xL1pR4tWvN3sD6f"

# 약한 비밀번호 → 패턴일치(엔트로피 낮음)
password = "password"

# 내부 서버 IP → "IP 주소"(검증됨, 낮음)
INTERNAL_SERVER_IP = "192.168.10.55"
