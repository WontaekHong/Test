import streamlit as st
import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="OCR 가계부 자동화", layout="centered")
st.title("📸 OCR 기반 3 모바일 가계부 자동 정리")

uploaded_file = st.file_uploader("이미지 업로드 (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.success("✅ 파일 업로드 성공!")

    # 이미지 열기 및 표시
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="업로드한 이미지", use_column_width=True)
    except Exception as e:
        st.error(f"❌ 이미지 열기 실패: {e}")
        st.stop()

    try:
        # OpenCV 전처리
        image_np = np.array(image)
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]

        # OCR
        text = pytesseract.image_to_string(thresh, lang='kor+eng')
        st.markdown("### 📝 OCR 인식된 텍스트")
        st.code(text)

        if not text.strip():
            st.warning("❗ OCR에서 텍스트를 추출하지 못했습니다. 더 선명한 이미지를 사용해 주세요.")
            st.stop()

        # 텍스트 파싱
        lines = text.split('\n')
        date_pattern = r"20\d{2}[.\-/년 ]\d{1,2}[.\-/월 ]\d{1,2}"
        current_date = ""

        category_map = {
            "편의점|식당|마차|배달|김밥|카페|커피|식사|밥|이츠|쿠팡이츠": "식비",
            "주유|세차|하이패스|톨게이트|자동차|캐피탈|오일": "자동차유지비",
            "SKT|KT|LGU|통신": "통신비",
            "미용|이발|파마|네일|왁싱|에스테틱": "미용",
            "도서|문구|서점|책": "도서",
            "결혼|장례|경조|부의|축의": "경조사",
            "용돈|송금|현금": "용돈",
            "보험|실비|건강보험": "보험",
            "기저귀|분유|육아|아기|아이|어린이집": "육아"
        }

        parsed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.search(date_pattern, line):
                current_date = re.sub(r"[^\d-]", "-", re.search(date_pattern, line).group()).strip("-")
                continue

            match = re.search(r"(-?\d{1,3}(,\d{3})*|\d{4,})", line.replace(" ", ""))
            if match:
                amount_str = match.group().replace(",", "")
                try:
                    amount = -abs(int(amount_str))
                except:
                    continue

                usage = line.replace(match.group(), "").strip()
                category = "기타"
                for pattern, cat in category_map.items():
                    if re.search(pattern, usage):
                        category = cat
                        break

                parsed.append({
                    "날짜": current_date,
                    "지출금액(원)": amount,
                    "사용처": usage,
                    "결제수단": "",
                    "카테고리": category,
                    "비고": ""
                })

        if parsed:
            df = pd.DataFrame(parsed)
            st.success("✅ 분석 완료! 아래에서 확인하세요")
            st.dataframe(df)

            # 엑셀 저장
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button(
                label="📥 엑셀 다운로드",
                data=output,
                file_name="가계부_OCR_자동정리.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ 텍스트는 인식됐지만, 지출 내역 파싱에는 실패했습니다.")
    except Exception as e:
        st.error(f"❌ 처리 중 오류 발생: {e}")
