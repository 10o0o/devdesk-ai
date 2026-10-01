"""KANT NEXT DevDesk. 정책 프롬프트부터 _todo(...) 한 곳씩 바꾸세요.

시작: uv run --frozen python main.py demo
확인: uv run --frozen python main.py check policy
실제 호출: uv run --frozen python main.py run policy --live

반복문, 파일 처리, 로그 형식은 준비되어 있습니다.
_todo(...)를 값, 조건식 또는 함수 호출로 바꾸면 해당 부분이 실행됩니다.
설명 주석에는 선택 이유를 1~2문장 남기세요. 별도 문서는 만들지 않습니다.
"""
import copy
import hashlib
import json
import re
import time

from jsonschema import Draft202012Validator, ValidationError

import support


def _todo(label):
    raise NotImplementedError(label)


# 필수 1 / 정책 프롬프트. 문자열 두 개를 작성합니다.
def build_instructions(documents, variant):
    if variant not in {"baseline", "reasoning"}:
        raise ValueError("variant는 baseline 또는 reasoning입니다.")
    # 이유: Few-shot과 Self-Consistency는 각각 어떤 상황에 쓰는지,
    # 이번에는 왜 Reasoning을 쓰는지와 한계를 2~3문장으로 적으세요.
    policy = _todo("정책 프롬프트: 역할, 업무 범위, 근거, 비밀정보, 담당자 확인, 답변 형식을 담은 문자열")
    if variant == "reasoning":
        policy += _todo("정책 프롬프트: 답변 전에 근거와 제약을 점검하게 하는 문자열")
    corpus = json.dumps(sorted(documents, key=lambda item: item["doc_id"]),
                        ensure_ascii=False, sort_keys=True)
    return policy + "\n<reference_documents>\n" + corpus + "\n</reference_documents>"


# 필수 2 / 답변 검증과 수정. 스키마를 만든 뒤 값과 출처를 검사합니다.
def answer_format():
    properties = _todo("답변 검증과 수정: answer, source_ids, needs_human, category의 JSON Schema 속성 dict")
    schema = {"type": "object", "properties": properties,
              "required": ["answer", "source_ids", "needs_human", "category"],
              "additionalProperties": False}
    return {"format": {"type": "json_schema", "name": "devdesk_answer",
                       "strict": True, "schema": schema}}


def validate_answer(raw, known_ids):
    answer = json.loads(raw)
    Draft202012Validator(answer_format()["format"]["schema"]).validate(answer)
    # 이유: 스키마를 통과해도 출처와 답변 본문을 따로 확인하는 이유를 적으세요.
    rules = [
        (_todo("답변 검증과 수정: answer가 공백뿐인지 판정하는 조건"), "blank answer"),
        (_todo("답변 검증과 수정: source_ids에 known_ids 밖의 값이 있는지 판정하는 조건"), "unknown source_id"),
        (_todo("답변 검증과 수정: source_ids에 중복이 있는지 판정하는 조건"), "duplicate source_id"),
        (_todo("답변 검증과 수정: 출처가 없는데 needs_human도 False인지 판정하는 조건"), "unsupported answer requires human"),
    ]
    for invalid, message in rules:
        if invalid:
            raise ValueError(message)
    return answer


def finish_answer(send, request, response, known_ids, events):
    request = copy.deepcopy(request)
    fallback = {"answer": "확인 가능한 답변을 만들지 못했습니다. 담당자 확인이 필요합니다.",
                "source_ids": [], "needs_human": True, "category": "general"}
    repair_used = False
    # 한 번 검사하고, 필요하면 한 번 수정한 뒤 같은 검사를 다시 합니다.
    for turn in range(2):
        if response is None:
            reason = "api_failure"
        elif response.get("status") == "round_limit":
            reason = "round_limit"
        elif response.get("status") != "completed":
            reason = "incomplete"
        elif support.has_refusal(response):
            reason = "refusal"
        else:
            try:
                answer = _todo("답변 검증과 수정: validate_answer에 응답 본문과 known_ids를 전달하는 호출")
                return {"answer": answer, "fallback_reason": None, "repair_used": repair_used}
            except (ValueError, ValidationError) as error:
                error_kind, field = support.validation_detail(error)
                events.append({"event": "validation_error", "repair_already_used": repair_used,
                               "error_kind": error_kind, "error_field": field})
                if turn == 1:
                    reason = "validation_failed"
                else:
                    # 종류: invalid_json, schema_error, blank_answer, unknown_source,
                    # duplicate_source, unsupported_answer. 종류에 맞게 안내를 만드세요.
                    hint = _todo("답변 검증과 수정: error_kind에 맞는 수정 안내 문자열")
                    repair_used = True
                    support.append_repair_input(request, response, hint)
                    response = _todo("답변 검증과 수정: send로 수정 요청을 전송하는 호출")
                    continue
        return {"answer": fallback, "fallback_reason": reason, "repair_used": repair_used}


# 필수 3 / 티켓 조회. 티켓 조회 조건과 모델에 돌려줄 값을 정합니다.
def tool_schema():
    parameters = _todo("티켓 조회: ticket_id 하나만 받는 object JSON Schema")
    return {"type": "function", "name": "lookup_ticket", "strict": True,
            "description": "기존 티켓의 상태를 읽습니다. 티켓을 변경하지 않습니다.",
            "parameters": parameters}


def execute_tool(name, arguments, tickets):
    if _todo("티켓 조회: 허용하지 않은 함수 이름인지 판정하는 조건"):
        return {"ok": False, "error": "unknown_tool"}
    try:
        args = json.loads(arguments)
        if _todo("티켓 조회: args가 dict가 아니거나 키가 ticket_id 하나가 아닌 조건. 키 누락도 포함"):
            raise ValueError("unexpected arguments")
        ticket_id = args["ticket_id"]
        if not isinstance(ticket_id, str) or not re.fullmatch(r"IT-[0-9]{4}", ticket_id):
            raise ValueError("invalid ticket_id")
    except (ValueError, TypeError):
        return {"ok": False, "error": "invalid_arguments"}
    if ticket_id not in tickets:
        return {"ok": False, "error": "not_found", "ticket_id": ticket_id}
    return {"ok": True, "ticket": _todo("티켓 조회: tickets에서 찾은 티켓의 사본")}


def tool_roundtrip(send, request, tickets, events):
    request = copy.deepcopy(request)
    for _ in range(4):
        response = send(request)
        if response is None or response.get("status") != "completed" or support.has_refusal(response):
            return request, response
        output = response.get("output", [])
        calls = [item for item in output if item.get("type") == "function_call"]
        if not calls:
            return request, response
        # 이유: 모델이 요청한 도구를 누가 실행하며 call_id를 왜 유지하는지 적으세요.
        request["input"].extend(_todo("티켓 조회: 이번 모델의 output 전체 사본"))
        for call in calls:
            if not isinstance(call.get("call_id"), str) or not call["call_id"]:
                return request, {"status": "incomplete", "output": []}
            result = _todo("티켓 조회: execute_tool에 함수 이름, 인자, tickets를 전달하는 호출")
            events.append({"event": "tool_result", "name": call.get("name"),
                           "call_id": call["call_id"], "ok": result["ok"], "error": result.get("error")})
            request["input"].append({"type": "function_call_output",
                                    "call_id": _todo("티켓 조회: 이번 함수 호출의 연결 ID"),
                                    "output": json.dumps(result, ensure_ascii=False)})
    return request, {"status": "round_limit", "output": []}


# 오류 화면 입력. 기존 텍스트 옆에 이미지 항목 하나를 추가합니다.
def image_content(question, image_path):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question is empty")
    content = [{"type": "input_text", "text": question}]
    if image_path is not None:
        content.append(_todo("오류 화면 입력: input_image 항목. support.image_url(image_path), detail='high' 사용"))
    # 이유: 화면에서 본 오류와 실제 장애 원인을 구분해야 하는 이유를 적으세요.
    return content


# 호출 재시도. 반복과 기록은 준비되어 있습니다. 다시 시도할 조건을 작성합니다.
def call_with_retry(send, request, events, sleep=time.sleep):
    for attempt in range(1, 4):
        started = time.perf_counter()
        try:
            response = send(request)
        except support.TransportError as error:
            status = error.status_code
            retryable = _todo("호출 재시도: timeout/connection/408/409/429/5xx만 허용하는 조건")
            retry_now = _todo("호출 재시도: 다시 시도할 수 있고 아직 3번째 시도가 아닌지 판정하는 조건")
            delay = support.delay_for(attempt) if retry_now else 0
            support.append_attempt(events, attempt, started, error=error,
                                   retryable=retryable, wait_s=delay)
            if not retry_now:
                return None
            sleep(delay)
        else:
            support.append_attempt(events, attempt, started, response=response)
            return response
    # 이유: 출력 수정과 전송 재시도가 다른 이유를 적으세요.


# 사용량과 비용. 고정 입력을 연결하고, 토큰을 골라 비용을 계산합니다.
def cache_settings(documents, variant):
    instructions = _todo("사용량과 비용: 정책 프롬프트의 고정 지시문을 만드는 호출")
    fingerprint = hashlib.sha256(instructions.encode("utf-8")).hexdigest()[:16]
    # 같은 정책과 조건은 같은 키를 사용합니다. 질문이나 현재 시각을 섞지 않습니다.
    return {"instructions": instructions,
            "prompt_cache_key": f"kant-next-pe-{variant}-{fingerprint}"}


def usage_record(attempt, prices):
    response = attempt.get("response") or {}
    usage = response.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    it = _todo("사용량과 비용: usage에서 전체 입력 토큰 읽기. 없으면 None")
    ot = _todo("사용량과 비용: usage에서 전체 출력 토큰 읽기. 없으면 None")
    cached = _todo("사용량과 비용: details에서 캐시 읽기 토큰 읽기. 없으면 None")
    written = details.get("cache_write_tokens")
    reasoning = (usage.get("output_tokens_details") or {}).get("reasoning_tokens")
    support.validate_usage_counters(it, ot, cached, written, reasoning)
    estimate, assumption = None, None
    if it is not None and ot is not None and cached is not None:
        effective_write = written if written is not None else 0
        if it > prices["max_input_tokens"]:
            assumption = "input exceeds the supplied price tier; estimate unavailable"
        else:
            if written is None:
                assumption = "cache_write_tokens absent; assumed zero for estimate"
            ordinary = _todo("사용량과 비용: 전체 입력에서 캐시 읽기와 쓰기를 뺀 일반 입력 수")
            # prices의 단가 키: input, cached, cache_write, output. 백만 토큰당 USD입니다.
            estimate = _todo("사용량과 비용: 일반 입력, 캐시 읽기, 캐시 쓰기, 출력 비용의 합을 백만으로 나누는 식")
    observation = _todo("사용량과 비용: cached가 None/양수/0일 때 unavailable/hit/miss를 고르는 식")
    # 이유: 캐시와 추론 토큰을 왜 중복 계산하지 않는지,
    # 두 요청의 비용이나 지연 차이를 전부 캐시 효과라 할 수 없는 이유를 적으세요.
    return support.pack_usage_record(attempt, response, prices, it, ot, cached, written,
                                     reasoning, observation, estimate, assumption)


# 전체 기능 연결. 준비된 실행 순서에 앞 함수들을 연결합니다.
def run_pipeline(send, question, documents, tickets, variant="reasoning",
                 image_path=None, prices=None, sleep=time.sleep):
    prices = support.load_prices() if prices is None else prices
    events = []
    started = time.perf_counter()
    settings = _todo("전체 기능 연결: cache_settings 호출")
    request = support.base_request(settings["instructions"], question, variant)
    request.update(settings)
    request["text"] = _todo("전체 기능 연결: 답변 형식을 만드는 함수 호출")
    request["tools"] = [_todo("전체 기능 연결: 도구 규격을 만드는 함수 호출")]
    request["parallel_tool_calls"] = False
    request["input"][0]["content"] = _todo("전체 기능 연결: 질문과 image_path로 입력을 만드는 함수 호출")

    def reliable_send(current_request):
        return call_with_retry(send, current_request, events, sleep=sleep)

    final_request, response = _todo("전체 기능 연결: tool_roundtrip에 reliable_send, request, tickets, events 전달")
    result = _todo("전체 기능 연결: finish_answer에 reliable_send, final_request, response, 문서 ID 집합, events 전달")
    result["tool_calls"] = sum(event["event"] == "tool_result" for event in events)
    result["logs"] = [usage_record(event, prices) if event["event"] == "api_attempt" else event
                      for event in events]
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    return result


# 선택 심화 1. 골격 없이 두 대상의 프롬프트와 비교 함수를 설계합니다.
def build_audience_instructions(documents, variant, audience):
    """newcomer/operator 지시를 직접 설계. 다른 모드는 ValueError.

    공통 정책을 유지하고, 용어 풀이와 처리 순서를 대상에 맞추세요.
    """
    raise NotImplementedError("선택 심화: build_audience_instructions를 작성하세요.")


def audit_audience_pair(newcomer, operator):
    """같은 질문의 유효한 답변 dict 두 개를 비교합니다.

    반환: same_policy(bool), different_explanation(bool), issues(list[str]).
    category, needs_human, source_ids 집합은 같아야 합니다.
    answer는 앞뒤 공백을 뺀 값이 달라야 합니다.
    issues에는 다른 정책 필드명과 필요하면 same_explanation을 담으세요.
    본문이 다르다는 사실만으로 설명이 적절하다고 결론내리지는 마세요.
    """
    raise NotImplementedError("선택 심화: audit_audience_pair를 작성하세요.")


if __name__ == "__main__":
    import sys
    raise SystemExit(support.cli(sys.modules[__name__]))
