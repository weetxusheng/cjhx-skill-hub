package com.ms.gateway.in.test;

import org.springframework.util.StringUtils;

import java.math.BigInteger;

public class MyEncode {

    private static int[] sub = { 33, 22, 32, 14, 7, 6 };
    public static String decode(String loginName, String sign) {
        if (StringUtils.isEmpty(loginName) ||StringUtils.isEmpty(sign)) {
            return null;
        }
        loginName = toStringHex(loginName);
        //name = toStringHex(name);
        loginName = loginName.substring(sub.length);
        byte[] bt = loginName.getBytes();
        byte[] btK = sign.getBytes();
        byte[] newB = new byte[1024];
        for (int i = 0; i < bt.length; i++) {
            String s = Integer.toBinaryString(bt[i]);
            int len = s.length();
            String startName = s.substring(0, len - 4);
            String endName = s.substring(len - 4);
            for (int j = 0; j < sign.length(); j++) {
                String keyB = Integer.toBinaryString(btK[j]);
                int lenK = keyB.length();
                String endNameK = keyB.substring(lenK - 4);
                endName = XOR(endName, endNameK);
            }
            String former = startName + endName;
            BigInteger src1 = new BigInteger(former, 2);
            newB[i] = src1.byteValue();
        }

        String decodeName = new String(newB).trim();
		/*if (!check_16(decodeName))
			return null;*/
        loginName = toStringHex(decodeName);
        return loginName;
    }

    public static String XOR(String name, String key) {
        String newValues = "";
        for (int i = 0; i < name.length(); i++) {
            String sum = String.valueOf(name.charAt(i))
                    + String.valueOf(key.charAt(i));
            int as = Integer.parseInt(sum);
            String newValue = "";
            switch (as) {
                case 10:
                    newValue = "1";
                    break;
                case 1:
                    newValue = "1";
                    break;
                case 11:
                    newValue = "0";
                    break;
                case 0:
                    newValue = "0";
                    break;
            }
            newValues += newValue;
        }
        return newValues;
    }


    public static String toStringHex(String s) {
        byte[] baKeyword = new byte[s.length() / 2];
        for (int i = 0; i < baKeyword.length; i++) {
            try {
                baKeyword[i] = (byte) (0xff & Integer.parseInt(
                        s.substring(i * 2, i * 2 + 2), 16));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        try {
            s = new String(baKeyword, "utf-8");// UTF-16le:Not
        } catch (Exception e) {
            e.printStackTrace();
        }
        return s;
    }
}
