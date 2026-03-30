"""主系统网关单点 `loginname`/`sign` 解码向量测试。"""

from app.services.sso_gateway_decode import decode_sso_login_name


def test_decode_sso_matches_java_sample():
    login_hex = "32754750696a3035303e30333063313e31333135303e303330633031"
    sign = (
        "HWUCTvjiVjgA5RP6pnw4a0uqGNcgspcFG2lP7AJ5Av4iw7nCBBpgoEnVfBtYzXEav71s8HDQ8Rp2RDa102gpqZg7ENveggnMqsHL"
    )
    assert decode_sso_login_name(login_hex, sign) == "chenxusheng"


def test_decode_sso_rejects_empty():
    assert decode_sso_login_name("", "x") is None
    assert decode_sso_login_name("ab", "") is None
