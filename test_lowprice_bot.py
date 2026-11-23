#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_lowprice_bot.py
lowprice_bot.py 파일의 4가지 핵심 요구사항을 가상 데이터만으로 엄격하게 검증하는 테스트 스크립트

[검사 내용]
1. 20,000원 이하일 때 특가 메시지가 출력되는가?
2. 20,000원 초과일 때 유지 메시지가 출력되는가?
3. 광고 상품이 섞여 있을 때 걸러낼 수 있는가?
4. 값을 가져오지 못했을 경우 멈추지 않고 오류를 알려주는가?

[검사 원칙]
1. 실제 외부 사이트(네이버/다나와 등)에 요청하지 않고 100% 가상 데이터만 사용
2. 항목마다 PASS/FAIL 여부를 상세 사유와 함께 목록으로 출력
3. 검사 항목을 지우거나 느슨하게 수정하지 않고 엄격한 기준 적용
"""

import contextlib
import io
import os
import sys
from typing import Callable, List, Tuple

# 테스트 대상 모듈 임포트
import lowprice_bot

# Windows 콘솔 한글 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1. 네트워크 호출 원천 차단 (가상 데이터만 사용 보장)
# ---------------------------------------------------------------------------
def blocked_network(*args, **kwargs):
    raise RuntimeError(
        "⛔ [네트워크 차단 위반] 테스트 중 실제 외부 네트워크 요청이 감지되었습니다! "
        "가상 데이터만 사용해야 합니다."
    )


lowprice_bot.urllib.request.urlopen = blocked_network


# ---------------------------------------------------------------------------
# 2. 가상 데이터 (Mock HTML) 정의
# ---------------------------------------------------------------------------

# 가상 데이터 1: 1위 가격이 20,000원 이하(17,860원)인 정상 데이터
MOCK_HTML_UNDER_20000 = """
<ul class="product_list">
  <li class="prod_item" id="productItem1001">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=1001">베베앙 쿠잉 베이직 아기물티슈 캡형 100매 20팩</a></p>
    <div class="price_sect"><strong>17,860</strong>원</div>
    <span class="mall_name">롯데ON</span>
    <span class="text__number">45</span>
  </li>
  <li class="prod_item" id="productItem1002">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=1002">베베앙 아기물티슈 러블리 핑크 캡형 100매 20팩</a></p>
    <div class="price_sect"><strong>19,890</strong>원</div>
    <span class="mall_name">11번가</span>
    <span class="text__number">120</span>
  </li>
  <li class="prod_item" id="productItem1003">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=1003">베베앙 더프라임 아기물티슈 캡형 72매 20팩</a></p>
    <div class="price_sect"><strong>20,810</strong>원</div>
    <span class="mall_name">G마켓</span>
    <span class="text__number">89</span>
  </li>
</ul>
"""

# 가상 데이터 2: 1위 가격이 20,000원 초과(22,900원)인 정상 데이터
MOCK_HTML_OVER_20000 = """
<ul class="product_list">
  <li class="prod_item" id="productItem2001">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=2001">베베앙 프리미엄 골드 물티슈 70매 20팩</a></p>
    <div class="price_sect"><strong>22,900</strong>원</div>
    <span class="mall_name">G마켓</span>
    <span class="text__number">215</span>
  </li>
  <li class="prod_item" id="productItem2002">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=2002">베베앙 오리지널 플러스 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>26,400</strong>원</div>
    <span class="mall_name">쿠팡</span>
    <span class="text__number">890</span>
  </li>
  <li class="prod_item" id="productItem2003">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=2003">베베앙 시그니처 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>29,800</strong>원</div>
    <span class="mall_name">11번가</span>
    <span class="text__number">430</span>
  </li>
</ul>
"""

# 가상 데이터 3: 광고 상품 및 판매불가 상품이 섞여 있는 가상 데이터
# (광고 2건, 품절 1건, 25매 1건, 정상 실판매 3건)
MOCK_HTML_WITH_ADS = """
<ul class="product_list">
  <li class="prod_item prod_ad_item" id="productItem9001">
    <span class="ico_ad">AD 애드스마트 광고상품</span>
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=9001">[광고] 초특가 스폰서 베베앙 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>5,000</strong>원</div>
    <span class="mall_name">스폰서광고몰</span>
    <span class="text__number">999</span>
  </li>
  <li class="prod_item power_link" id="productItem9002">
    <span class="ad_mark">광고</span>
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=9002">파워쇼핑 광고 베베앙 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>7,000</strong>원</div>
    <span class="mall_name">파워링크몰</span>
    <span class="text__number">88</span>
  </li>
  <li class="prod_item" id="productItem9003">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=9003">베베앙 단종 품절 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>일시품절</strong></div>
    <span class="mall_name">품절몰</span>
    <span class="text__number">10</span>
  </li>
  <li class="prod_item" id="productItem9004">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=9004">베베앙 휴대용 물티슈 캡형 25매 20팩</a></p>
    <div class="price_sect"><strong>12,000</strong>원</div>
    <span class="mall_name">휴대몰</span>
    <span class="text__number">77</span>
  </li>
  <li class="prod_item" id="productItem3001">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=3001">베베앙 실제판매 1위 물티슈 70매 20팩</a></p>
    <div class="price_sect"><strong>17,900</strong>원</div>
    <span class="mall_name">옥션</span>
    <span class="text__number">150</span>
  </li>
  <li class="prod_item" id="productItem3002">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=3002">베베앙 실제판매 2위 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>21,000</strong>원</div>
    <span class="mall_name">G마켓</span>
    <span class="text__number">260</span>
  </li>
  <li class="prod_item" id="productItem3003">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=3003">베베앙 실제판매 3위 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong>24,500</strong>원</div>
    <span class="mall_name">11번가</span>
    <span class="text__number">310</span>
  </li>
</ul>
"""

# 가상 데이터 4: 가격 또는 필수 값이 비어 있는 비정상 가상 데이터
MOCK_HTML_MISSING_VALUE = """
<ul class="product_list">
  <li class="prod_item" id="productItem4001">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=4001">베베앙 가격누락 오류 물티슈 100매 20팩</a></p>
    <div class="price_sect"><strong></strong></div>
    <span class="mall_name">11번가</span>
    <span class="text__number">100</span>
  </li>
  <li class="prod_item" id="productItem4002">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=4002">베베앙 정상 물티슈 100매 20팩 B</a></p>
    <div class="price_sect"><strong>19,000</strong>원</div>
    <span class="mall_name">G마켓</span>
    <span class="text__number">200</span>
  </li>
  <li class="prod_item" id="productItem4003">
    <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=4003">베베앙 정상 물티슈 100매 20팩 C</a></p>
    <div class="price_sect"><strong>22,000</strong>원</div>
    <span class="mall_name">옥션</span>
    <span class="text__number">300</span>
  </li>
</ul>
"""


# ---------------------------------------------------------------------------
# 3. 4대 검사 함수 구현
# ---------------------------------------------------------------------------

def check_1_under_20000() -> Tuple[bool, str]:
    """1. 20,000원 이하일 때 특가 메시지가 출력되는가?"""
    products = lowprice_bot.search_danawa_lowest(
        keyword="베베앙 20개", top_n=3, html_source=MOCK_HTML_UNDER_20000
    )
    if len(products) != 3:
        return False, f"상품 3개가 반환되지 않음 (반환 수: {len(products)})"

    first_price = int(products[0]["price"])
    if first_price > 20000:
        return False, f"1위 가격({first_price:,}원)이 20,000원을 초과함"

    # 콘솔 출력 캡처
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lowprice_bot.print_results(
            "베베앙 20개", products, target_price=20000, send_kakao=False
        )
    output = buf.getvalue()

    expected_msg = "[특가발견] 목표가격이하입니다."
    if expected_msg not in output:
        return False, f"출력 화면에 '{expected_msg}' 문구가 누락됨. (실제 출력: {output})"

    return True, f"1위 가격({first_price:,}원) <= 20,000원 확인 및 '{expected_msg}' 정확히 출력됨"


def check_2_over_20000() -> Tuple[bool, str]:
    """2. 20,000원 초과일 때 유지 메시지가 출력되는가?"""
    products = lowprice_bot.search_danawa_lowest(
        keyword="베베앙 20개", top_n=3, html_source=MOCK_HTML_OVER_20000
    )
    if len(products) != 3:
        return False, f"상품 3개가 반환되지 않음 (반환 수: {len(products)})"

    first_price = int(products[0]["price"])
    if first_price <= 20000:
        return False, f"1위 가격({first_price:,}원)이 20,000원 이하임"

    # 콘솔 출력 캡처
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lowprice_bot.print_results(
            "베베앙 20개", products, target_price=20000, send_kakao=False
        )
    output = buf.getvalue()

    expected_msg = "[유지] 아직 목표 가격보다 비싸요!"
    unexpected_msg = "[특가발견] 목표가격이하입니다."

    if expected_msg not in output:
        return False, f"출력 화면에 '{expected_msg}' 문구가 누락됨."
    if unexpected_msg in output:
        return False, f"20,000원 초과인데 특가 메시지('{unexpected_msg}')가 잘못 출력됨."

    return True, f"1위 가격({first_price:,}원) > 20,000원 확인 및 '{expected_msg}' 정확히 출력됨"


def check_3_filter_ads() -> Tuple[bool, str]:
    """3. 광고 상품이 섞여 있을 때 걸러낼 수 있는가?"""
    products = lowprice_bot.search_danawa_lowest(
        keyword="베베앙 20개", top_n=3, html_source=MOCK_HTML_WITH_ADS
    )
    if len(products) != 3:
        return False, f"광고/품절/25매 제외 후 실제 상품 3개가 추출되지 않음 (추출 수: {len(products)})"

    titles = [str(p["title"]) for p in products]
    prices = [int(p["price"]) for p in products]

    # 광고 상품(5,000원, 7,000원), 품절 상품, 25매 상품(12,000원)이 포함되어 있는지 검사
    for t in titles:
        for forbidden in ("광고", "파워쇼핑", "스폰서", "단종", "품절", "25매"):
            if forbidden in t:
                return False, f"제외되어야 할 비정상/광고 상품('{forbidden}')이 결과에 포함됨: {t}"

    # 실제 판매 상품 3건의 최저가 정렬 순서 검증 (17,900원 -> 21,000원 -> 24,500원)
    if prices != [17900, 21000, 24500]:
        return False, f"실제 판매 상품의 최저가 순 정렬이 올바르지 않음 (실제: {prices}, 기대값: [17900, 21000, 24500])"

    return True, f"광고 2건·품절 1건·25매 1건 완벽 필터링 완료, 실제 판매 상품 3건({prices}) 정상 선별"


def check_4_missing_values_reporting() -> Tuple[bool, str]:
    """4. 값을 가져오지 못했을 경우 멈추지 않고 오류를 알려주는가?"""
    # 가격 등 필수 값이 비어 있는 비정상 데이터를 주입했을 때
    # 1) 프로그램이 제어 불능 상태(Crash)로 그냥 죽지 않고
    # 2) 임의의 가짜 값을 지어내지도 않으며
    # 3) 무엇이 잘못되었는지 정확한 오류 원인(BotValidationError)을 명확히 보고하는지 검증
    try:
        lowprice_bot.search_danawa_lowest(
            keyword="베베앙 20개", top_n=3, html_source=MOCK_HTML_MISSING_VALUE
        )
        return False, "필수 값(가격)이 비어 있는데도 오류를 알리지 않고 임의 통과/지어냄"
    except lowprice_bot.BotValidationError as bve:
        err_msg = str(bve)
        # 구체적인 원인(가격 필드 오류)이 오류 메시지에 명시되어 있는지 확인
        if "가격(price)" not in err_msg and "데이터 검증 실패" not in err_msg:
            return False, f"오류 메시지에 구체적인 원인이 명시되지 않음: {err_msg}"
        return True, f"비정상 종료 없이 오류 원인을 사용자에게 정확히 보고함 ('{err_msg}')"
    except Exception as exc:
        return False, f"제어되지 않은 예외(Crash) 발생: {type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# 4. 전체 검사 실행 및 리포트 출력
# ---------------------------------------------------------------------------

def run_tests() -> bool:
    test_cases: List[Tuple[str, Callable[[], Tuple[bool, str]]]] = [
        ("1. 20,000원 이하 일 때 특가 메세지가 출력되는가?", check_1_under_20000),
        ("2. 20,000원 초과 일 때 유지 메세지가 출력되는가?", check_2_over_20000),
        ("3. 광고 상품이 섞여 있을 때 걸러낼 수 있는가?", check_3_filter_ads),
        ("4. 값을 가져오지 못했을 경우 멈추지 않고 오류를 알려주는가?", check_4_missing_values_reporting),
    ]

    print("=" * 82)
    print("🧪 [lowprice_bot.py 자동 검증 테스트]")
    print("   ※ 외부 사이트 요청 0건 (100% 가상 데이터 기반 엄격 검증)")
    print("=" * 82)

    all_passed = True
    for idx, (title, func) in enumerate(test_cases, start=1):
        try:
            passed, reason = func()
        except Exception as e:
            passed = False
            reason = f"검사 중 예외 발생: {type(e).__name__}: {e}"

        status = "PASS" if passed else "FAIL"
        icon = "✅" if passed else "❌"
        print(f"{icon} [{status}] {title}")
        print(f"   └─ 결과: {reason}")
        if not passed:
            all_passed = False

    print("=" * 82)
    if all_passed:
        print("🎉 [최종 결과] 4개 검사 항목 모두 [PASS] 달성 완료!")
    else:
        print("⚠️ [최종 결과] 일부 검사 항목이 [FAIL] 되었습니다. 수정이 필요합니다.")
    print("=" * 82)
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
