#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
issue_kakao_token.py
.env 파일의 KAKAO_REST_API_KEY와 KAKAO_CLIENT_SECRET, 그리고 인가 코드(Authorization Code)를 사용해
카카오 리프레시 토큰(KAKAO_REFRESH_TOKEN)을 발급받아 .env 파일에 자동으로 추가/갱신하는 스크립트입니다.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
TOKEN_URL = "https://kauth.kakao.com/oauth/token"
DEFAULT_REDIRECT_URI = "http://localhost"


def load_env(path: str = DEFAULT_ENV_PATH) -> dict:
    env_vars = {}
    if not os.path.exists(path):
        raise FileNotFoundError(f".env 파일이 존재하지 않습니다: {path}")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def save_refresh_token_to_env(path: str, refresh_token: str) -> None:
    """새로 발급받은 refresh_token을 .env 파일에 추가하거나 기존 항목을 갱신합니다."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"KAKAO_REFRESH_TOKEN={refresh_token}\n")
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("KAKAO_REFRESH_TOKEN="):
            new_lines.append(f"KAKAO_REFRESH_TOKEN={refresh_token}\n")
            updated = True
        else:
            if not line.endswith("\n"):
                line += "\n"
            new_lines.append(line)

    if not updated:
        new_lines.append(f"KAKAO_REFRESH_TOKEN={refresh_token}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def request_kakao_token(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
) -> dict:
    """카카오 토큰 발급 API를 호출하여 access_token 및 refresh_token을 발급받습니다."""
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {err_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"네트워크 접속 실패: {e.reason}") from e


def issue_and_save(code: str, env_path: str = DEFAULT_ENV_PATH, redirect_uri: str = DEFAULT_REDIRECT_URI) -> str:
    env_vars = load_env(env_path)
    client_id = env_vars.get("KAKAO_REST_API_KEY")
    client_secret = env_vars.get("KAKAO_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(".env 파일에 KAKAO_REST_API_KEY 또는 KAKAO_CLIENT_SECRET이 누락되었습니다.")

    result = request_kakao_token(client_id, client_secret, code, redirect_uri)
    refresh_token = result.get("refresh_token")
    if not refresh_token:
        raise RuntimeError(f"응답에 refresh_token이 포함되어 있지 않습니다: {result}")

    save_refresh_token_to_env(env_path, refresh_token)
    return refresh_token


def main() -> int:
    parser = argparse.ArgumentParser(description="카카오 리프레시 토큰 발급 및 .env 자동 저장 도구")
    parser.add_argument("--code", required=True, help="카카오 인가 코드 (Authorization Code)")
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI, help="Redirect URI (기본값: http://localhost)")
    parser.add_argument("--env-file", default=DEFAULT_ENV_PATH, help=".env 파일 경로 (기본값: 동일 폴더 .env)")
    args = parser.parse_args()

    try:
        refresh_token = issue_and_save(args.code, env_path=args.env_file, redirect_uri=args.redirect_uri)
        print("=" * 70)
        print("🎉 [발급 및 저장 성공] 카카오 리프레시 토큰이 정상 발급되었습니다!")
        print(f"📁 저장 위치: {args.env_file}")
        print(f"🔑 KAKAO_REFRESH_TOKEN={refresh_token}")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"⛔ [카카오 토큰 발급 실패] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
