"""主系统网关单点登录参数解码（与历史 Java `MyEncode.decode` 算法一致）。

主系统跳转时在 URL 上携带十六进制编码的 `loginname` 与 `sign`（密钥字节流），
解码后得到本地用户名（`users.username`），供门户免密换发 JWT。

参考实现见仓库 `docs/20-engineering/references/sso-gateway-MyEncode.java`。
"""

from __future__ import annotations

SUB_PREFIX_LEN = 6


def _hex_to_utf8_string(s: str) -> str:
    return bytes.fromhex(s).decode("utf-8")


def _java_int_to_binary_string(i: int) -> str:
    ui = i & 0xFFFFFFFF
    if i < 0:
        return format(ui, "032b")
    return bin(ui & 0xFFFFFFFF)[2:]


def _byte_to_binary_string(b: int) -> str:
    signed = b if b < 128 else b - 256
    return _java_int_to_binary_string(signed)


def _xor_end(name4: str, key4: str) -> str:
    newv: list[str] = []
    for i in range(4):
        a, k = name4[i], key4[i]
        sm = int(str(a) + str(k))
        if sm in (10, 1):
            newv.append("1")
        elif sm in (11, 0):
            newv.append("0")
        else:
            msg = f"单点解码 XOR 遇到非法位对: {a!r}{k!r}"
            raise ValueError(msg)
    return "".join(newv)


def decode_sso_login_name(login_name_hex: str, sign: str) -> str | None:
    """将 URL 中的 `loginname`（hex）与 `sign` 解码为明文用户名。

    返回:
    - 成功时为用户名字符串；参数为空或解码失败时返回 ``None``（不抛异常，由上层决定 HTTP 状态）。
    """
    if not login_name_hex or not sign:
        return None
    try:
        login_name = _hex_to_utf8_string(login_name_hex)
        login_name = login_name[SUB_PREFIX_LEN:]
        bt = list(login_name.encode("utf-8"))
        new_b = bytearray(len(bt))
        sign_bytes = sign.encode("latin-1")

        for i in range(len(bt)):
            s = _byte_to_binary_string(bt[i])
            ln = len(s)
            if ln < 4:
                return None
            start_name = s[: ln - 4]
            end_name = s[ln - 4 :]
            for j in range(len(sign)):
                key_b = _byte_to_binary_string(sign_bytes[j])
                len_k = len(key_b)
                if len_k < 4:
                    return None
                end_name_k = key_b[len_k - 4 :]
                end_name = _xor_end(end_name, end_name_k)
            former = start_name + end_name
            new_b[i] = int(former, 2) & 0xFF

        decode_name = bytes(new_b).decode("utf-8").strip("\x00").strip()
        return _hex_to_utf8_string(decode_name)
    except (ValueError, UnicodeDecodeError, OSError):
        return None
