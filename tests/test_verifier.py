"""Test 1: Fake-Quote Verification Test.

Rule R3: Feed a response with an invented quote; verify it is downgraded to Unclear.
"""

from engine.verifier import verify_quote


def test_fake_quote_downgraded():
    source_resume = "Sarah Chen has 5 years of experience architecting backend microservices in Python 3.11 with asyncio."

    # 1. Real quote test
    real_quote = "5 years of experience architecting backend microservices in Python 3.11 with asyncio"
    is_valid, quote_res, msg = verify_quote(source_resume, real_quote)
    assert is_valid is True, "Valid quote should verify successfully"
    assert quote_res == real_quote

    # 2. Fabricated / Invented quote test
    invented_quote = "Architected ultra-low latency distributed payment gateways handling 2 million transactions per second"
    is_fake_valid, fake_res, fake_msg = verify_quote(source_resume, invented_quote)
    assert is_fake_valid is False, "Invented quote must fail verification"
    assert fake_res is None, "Invented quote must return None"
    assert "could not be verified" in fake_msg, "Should log unverified quote message"
    return True


if __name__ == "__main__":
    test_fake_quote_downgraded()
    print("PASS: test_fake_quote_downgraded")
