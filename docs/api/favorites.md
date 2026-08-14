# 즐겨찾기 API 명세서

> 현재 인증은 실제 로그인 대신 Mock 사용자를 사용합니다.  
> Swagger: http://localhost:8000/docs

> `facility_id`는 내부 DB 시설(UUID)뿐 아니라 카카오 로컬 실시간 결과(place id 문자열,
> 카페/병원/편의점)도 저장할 수 있습니다. `source`(`internal` | `kakao`)로 구분하며,
> `internal`만 저장 시점에 시설 존재 여부를 검증합니다. `kakao`는 재조회 시 카카오 API
> 쿼터가 소모되므로 검증 없이 프론트가 넘긴 값을 그대로 신뢰합니다.

---

## 1. 즐겨찾기 목록 조회

### 기본 정보

- Method: `GET`
- URL: `/favorites/lists`
- 설명: 현재 사용자의 고정 즐겨찾기 목록 3개와 목록별 즐겨찾기 개수를 조회합니다.

### 요청

Path Parameter, Query Parameter, Request Body가 없습니다.

### 성공 응답

- Status Code: `200 OK`

```json
[
  {
    "id": "4bd8b578-b03e-4f23-a8b2-f489fb92df92",
    "list_type": "FREQUENT",
    "created_at": "2026-07-28T05:00:00",
    "favorite_count": 0
  },
  {
    "id": "c377b8bb-6659-4586-b6a8-94a859d2d38a",
    "list_type": "WISHLIST",
    "created_at": "2026-07-28T05:00:00",
    "favorite_count": 2
  },
  {
    "id": "41cc913c-c842-45cf-a7ae-7df29b639687",
    "list_type": "VISITED",
    "created_at": "2026-07-28T05:00:00",
    "favorite_count": 1
  }
]
```

### 응답 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | UUID | 즐겨찾기 목록 ID |
| `list_type` | String | 즐겨찾기 목록 종류 |
| `created_at` | DateTime | 목록 생성 시각 |
| `favorite_count` | Integer | 해당 목록에 저장된 즐겨찾기 개수 |

### list_type 종류

| 값 | 설명 |
|---|---|
| `FREQUENT` | 자주 가는 장소 |
| `WISHLIST` | 가고 싶은 장소 |
| `VISITED` | 방문한 장소 |

저장된 즐겨찾기가 없는 목록은 `favorite_count: 0`으로 반환됩니다.

---

## 2. 특정 즐겨찾기 목록 항목 조회

### 기본 정보

- Method: `GET`
- URL: `/favorites/lists/{list_id}`
- 설명: 특정 즐겨찾기 목록에 저장된 항목을 조회합니다.
- 정렬 기준: `created_at DESC`
- 정렬 방식: 최근 저장한 항목부터 반환합니다.

### Path Parameter

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `list_id` | UUID | 필수 | 조회할 즐겨찾기 목록 ID |

### 요청 예시

```http
GET /favorites/lists/4bd8b578-b03e-4f23-a8b2-f489fb92df92
```

### 성공 응답

- Status Code: `200 OK`

```json
[
  {
    "id": "e32eab8e-4245-46ab-8127-bae565732668",
    "facility_id": "a81bac94-e01e-40d2-9056-195564766021",
    "source": "internal",
    "list_id": "4bd8b578-b03e-4f23-a8b2-f489fb92df92",
    "created_at": "2026-07-28T06:20:00"
  },
  {
    "id": "f24135bb-90bb-4a76-97f0-4052781dff04",
    "facility_id": "521460056",
    "source": "kakao",
    "list_id": "4bd8b578-b03e-4f23-a8b2-f489fb92df92",
    "created_at": "2026-07-28T06:10:00"
  }
]
```

### 응답 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | UUID | 즐겨찾기 항목 ID |
| `facility_id` | String | 저장된 시설 ID (internal=UUID 문자열, kakao=place id 문자열) |
| `source` | String | 시설 출처 (`internal` \| `kakao`) |
| `list_id` | UUID | 항목이 속한 목록 ID |
| `created_at` | DateTime | 즐겨찾기 저장 시각 |

### 빈 목록 응답

목록은 존재하지만 저장된 항목이 없는 경우:

- Status Code: `200 OK`

```json
[]
```

### 존재하지 않거나 현재 사용자 소유가 아닌 목록

- Status Code: `404 Not Found`

```json
{
  "detail": "즐겨찾기 목록을 찾을 수 없습니다."
}
```

---

## 3. 즐겨찾기 저장

### 기본 정보

- Method: `POST`
- URL: `/favorites`
- 설명: 특정 시설을 선택한 즐겨찾기 목록에 저장합니다.

### Request Body

```json
{
  "facility_id": "a81bac94-e01e-40d2-9056-195564766021",
  "source": "internal",
  "list_id": "4bd8b578-b03e-4f23-a8b2-f489fb92df92"
}
```

### 요청 필드

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `facility_id` | String | 필수 | 저장할 시설 ID (internal=UUID 문자열, kakao=place id 문자열) |
| `source` | String | 선택 (기본값 `internal`) | 시설 출처 (`internal` \| `kakao`) |
| `list_id` | UUID | 필수 | 저장할 즐겨찾기 목록 ID |

### 성공 응답

- Status Code: `201 Created`

```json
{
  "id": "e32eab8e-4245-46ab-8127-bae565732668",
  "facility_id": "a81bac94-e01e-40d2-9056-195564766021",
  "source": "internal",
  "list_id": "4bd8b578-b03e-4f23-a8b2-f489fb92df92",
  "created_at": "2026-07-28T06:20:00"
}
```

### 존재하지 않거나 현재 사용자 소유가 아닌 목록

- Status Code: `404 Not Found`

```json
{
  "detail": "즐겨찾기 목록을 찾을 수 없습니다."
}
```

### 존재하지 않는 시설 (`source: "internal"`만 해당)

`source`가 `kakao`인 경우 존재 검증을 하지 않으므로 이 오류는 발생하지 않습니다.

- Status Code: `404 Not Found`

```json
{
  "detail": "시설을 찾을 수 없습니다."
}
```

### facility_id 형식이 source와 맞지 않는 경우

`source: "internal"`인데 `facility_id`가 UUID 형식이 아닌 경우:

- Status Code: `422 Unprocessable Entity`

```json
{
  "detail": "internal 시설의 facility_id는 UUID 형식이어야 합니다."
}
```

### 중복 저장

같은 시설을 같은 즐겨찾기 목록에 다시 저장하는 경우:

- Status Code: `409 Conflict`

```json
{
  "detail": "이미 해당 목록에 저장된 시설입니다."
}
```

같은 시설을 서로 다른 목록에 저장하는 것은 허용됩니다.

---

## 4. 즐겨찾기 삭제

### 기본 정보

- Method: `DELETE`
- URL: `/favorites/{favorite_id}`
- 설명: 저장된 즐겨찾기 항목을 삭제합니다.

### Path Parameter

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `favorite_id` | UUID | 필수 | 삭제할 즐겨찾기 항목 ID |

### 요청 예시

```http
DELETE /favorites/e32eab8e-4245-46ab-8127-bae565732668
```

### 성공 응답

- Status Code: `204 No Content`
- Response Body: 없음

### 존재하지 않거나 현재 사용자 소유가 아닌 즐겨찾기

- Status Code: `404 Not Found`

```json
{
  "detail": "즐겨찾기를 찾을 수 없습니다."
}
```

---

## 5. 시설 즐겨찾기 상태 조회

### 기본 정보

- Method: `GET`
- URL: `/favorites/{facility_id}/status`
- 설명: 특정 시설이 현재 사용자의 즐겨찾기 목록에 저장되어 있는지 확인합니다.

### Path Parameter

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `facility_id` | String | 필수 | 즐겨찾기 상태를 조회할 시설 ID (internal=UUID 문자열, kakao=place id 문자열) |

### Query Parameter

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `source` | String | 선택 (기본값 `internal`) | 시설 출처 (`internal` \| `kakao`) |

### 요청 예시

```http
GET /favorites/a81bac94-e01e-40d2-9056-195564766021/status?source=internal
GET /favorites/521460056/status?source=kakao
```

### 즐겨찾기에 저장된 경우

- Status Code: `200 OK`

```json
{
  "is_favorite": true,
  "favorite_list_ids": [
    "4bd8b578-b03e-4f23-a8b2-f489fb92df92"
  ]
}
```

### 여러 목록에 저장된 경우

```json
{
  "is_favorite": true,
  "favorite_list_ids": [
    "4bd8b578-b03e-4f23-a8b2-f489fb92df92",
    "c377b8bb-6659-4586-b6a8-94a859d2d38a"
  ]
}
```

### 저장되지 않은 경우

- Status Code: `200 OK`

```json
{
  "is_favorite": false,
  "favorite_list_ids": []
}
```

### 존재하지 않는 시설 (`source: "internal"`만 해당)

`source`가 `kakao`인 경우 존재 검증을 하지 않으므로 이 오류는 발생하지 않습니다.

- Status Code: `404 Not Found`

```json
{
  "detail": "시설을 찾을 수 없습니다."
}
```

### 응답 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `is_favorite` | Boolean | 해당 시설의 즐겨찾기 저장 여부 |
| `favorite_list_ids` | UUID Array | 해당 시설이 저장된 즐겨찾기 목록 ID 배열 |

---

## 6. 공통 오류 응답

UUID 형식이 잘못된 값을 전달한 경우 FastAPI 입력 검증에 의해 다음 응답이 반환될 수 있습니다.

- Status Code: `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": [
        "path",
        "list_id"
      ],
      "msg": "Input should be a valid UUID",
      "input": "잘못된 UUID"
    }
  ]
}
```

---

## 7. 테스트 완료 항목

- 즐겨찾기 목록 3개 조회
- 목록별 `favorite_count` 반환
- 빈 목록 조회 시 빈 배열 반환
- 존재하지 않는 목록 조회 시 `404`
- 존재하지 않는 시설 저장 시 `404`
- 같은 시설 중복 저장 시 `409`
- 존재하지 않는 즐겨찾기 삭제 시 `404`
- 즐겨찾기 최신순 정렬
- `favorite_count`와 실제 저장 항목 개수 일치
- `source: "internal"`인데 `facility_id`가 UUID가 아니면 `422`
- `source: "kakao"`는 존재 검증 없이 저장 및 상태 조회 가능
- pytest 테스트 10개 통과