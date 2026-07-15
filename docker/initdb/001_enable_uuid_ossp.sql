-- uuid-ossp 확장 활성화 (컨테이너 최초 생성 시 1회 실행됨)
-- 확정 스키마의 모든 PK가 uuid_generate_v4()를 기본값으로 사용한다.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
