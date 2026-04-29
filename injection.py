import re
from dataclasses import dataclass
from enum import IntEnum
from typing import List


class RiskLevel(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Finding:
    pattern: str
    message: str
    risk: RiskLevel
    match_snippet: str = ""


# Heuristic rules (education / demo) — not a substitute for parameterization
_PATTERNS: list[tuple[str, str, RiskLevel, str | None]] = [
    (r"(?i)\bOR\s+['\"]?\d*['\"]?=\s*['\"]?\d*['\"]?", "Classic tautology in boolean context", RiskLevel.CRITICAL, None),
    (r"(?i)\bOR\s+['\"]1['\"]\s*=\s*['\"]1['\"]", "Tautology: OR '1'='1'", RiskLevel.CRITICAL, None),
    (r"(?i)\bUNION\s+SELECT\b", "UNION-based injection (UNION SELECT)", RiskLevel.CRITICAL, None),
    (r"(?i);[\s\n]*(DROP|TRUNCATE|ALTER|CREATE)\b", "Stacked command after semicolon", RiskLevel.CRITICAL, None),
    (r"(?i)EXEC(\s+|\()", "Execute / exec-style payload", RiskLevel.CRITICAL, None),
    (r"(?i)\bxp_\w+", "Extended stored procedure (xp_*)", RiskLevel.HIGH, None),
    (r"(?i)\bSLEEP\s*\(|\bBENCHMARK\s*\(|\bWAITFOR\s+DELAY\b", "Time-based blind SQL patterns", RiskLevel.HIGH, None),
    (r"(?i)INTO\s+OUTFILE|LOAD_FILE\s*\(", "File read / write patterns", RiskLevel.HIGH, None),
    (r"(?i)/\*.*?\*/", "Block comment (often used to bypass filters)", RiskLevel.MEDIUM, None),
    (r"(?i)--\s*[^
]+|\#[^
]*", "Line comment in expression (often to truncate server-side query)", RiskLevel.MEDIUM, None),
    (r"(?i)\bINFORMATION_SCHEMA\b|\bSYS\.\b|\bpg_catalog\b", "Metadata catalog access", RiskLevel.MEDIUM, None),
    (r"(?i)\bCHAR\s*\(\s*\d", "CHAR() concatenation (obfuscation)", RiskLevel.MEDIUM, None),
    (r"(?i)CONCAT\s*\(|0x[0-9a-fA-F]+", "String concatenation / hex literals", RiskLevel.LOW, None),
]


def analyze_injection(text: str) -> dict:
    """
    Scan raw SQL for common injection-style patterns.
    
    This function analyzes SQL queries for potential injection vulnerabilities
    using regex-based pattern matching.
    
    Args:
        text (str): The SQL query string to analyze.
    
    Returns:
        dict: A dictionary containing:
            - "level" (str): Risk level as string (low, medium, high, critical)
            - "level_num" (int): Risk level as integer
            - "findings" (list): List of detected patterns with details
    """
    if not text or not str(text).strip():
        return {
            "level": "low",
            "level_num": int(RiskLevel.LOW),
            "findings": [],
        }
    s = str(text)
    findings: List[Finding] = []
    seen: set[str] = set()

    for regex, message, risk, _ in _PATTERNS:
        for m in re.finditer(regex, s, re.DOTALL):
            key = f"{m.start()}:{m.end()}:{message}"
            if key in seen:
                continue
            seen.add(key)
            snippet = m.group(0)
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            findings.append(
                Finding(
                    pattern=regex,
                    message=message,
                    risk=risk,
                    match_snippet=snippet,
                )
            )

    max_risk = RiskLevel.LOW
    if findings:
        max_risk = max(f.risk for f in findings)
    level_names = {RiskLevel.LOW: "low", RiskLevel.MEDIUM: "medium", RiskLevel.HIGH: "high", RiskLevel.CRITICAL: "critical"}
    return {
        "level": level_names[max_risk],
        "level_num": int(max_risk),
        "findings": [
            {
                "pattern": f.pattern,
                "message": f.message,
                "risk": level_names[f.risk],
                "snippet": f.match_snippet,
            }
            for f in sorted(findings, key=lambda x: -int(x.risk))
        ],
    }