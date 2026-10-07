"""RoboDog: 전진 중 지정 QR을 만나면 왼쪽 90도 회전 후 계속 전진."""

from threading import Event
from time import monotonic

from kocoafab_robodog import *


# 로보독 설정
PORT = "COM15"
MOVE_SPEED = 15
TURN_SPEED = 35

# QR 이름
FIRE_QR_NAME = "fire"
WARNING_QR_NAME = "warning"
GROUND_QR_NAME = "ground"

# 왼쪽으로 회전할 QR
LEFT_TURN_QR_NAMES = {
    FIRE_QR_NAME,
    WARNING_QR_NAME,
    GROUND_QR_NAME,
}


dog = RoboDog()

try:
    # 로보독 연결
    if not dog.Open(PORT):
        raise RuntimeError(f"{PORT} 연결 실패")

    print("로보독 연결 성공")

    # QR 인식 모드 시작
    mode_response = dog.ai_mode(QRCODE_READ, timeout=5.0)
    print("QR 모드 응답:", mode_response)
    print("AI 보드 연결:", dog.is_ai_alive())

    # 안정 자세
    print("안정 자세 준비")
    dog.leg_bend(ALL_LEG, 60)
    Event().wait(2.0)

    # 전진 시작
    print("전진 시작")
    dog.move(FORWARD, MOVE_SPEED)

    next_debug_time = monotonic()
    handled_qr = None
    qr_missing_count = 0

    while True:
        qr_name = dog.get_qrcode()

        if qr_name:
            qr_name = str(qr_name).strip().lower()
            qr_missing_count = 0

            # fire, warning, ground이면 왼쪽 90도 회전
            if qr_name in LEFT_TURN_QR_NAMES and qr_name != handled_qr:
                handled_qr = qr_name

                print("QR 인식:", qr_name)

                # 앉지 않고 전진만 정지
                dog.move(STOP)

                print(qr_name, "감지 - 왼쪽으로 90도 회전")

                # 왼쪽으로 90도 회전
                dog.rotate(CCW, 90, TURN_SPEED)

                # 다시 전진
                dog.move(FORWARD, MOVE_SPEED)

                print("회전 완료 - 다시 전진")

        else:
            qr_missing_count += 1

            # QR이 약 0.5초 동안 보이지 않으면 다시 인식 허용
            if qr_missing_count >= 10:
                handled_qr = None

        # 1초마다 AI 데이터 출력
        if monotonic() >= next_debug_time:
            print(
                "QR 대기 / AI 데이터:",
                list(dog.get_ai_data())
            )
            next_debug_time = monotonic() + 1.0

        # time.sleep()은 이동을 자동 정지시킬 수 있으므로 사용하지 않음
        Event().wait(0.05)

except KeyboardInterrupt:
    print("사용자 긴급 정지")

finally:
    try:
        dog.move(STOP)
        dog.spin(STOP)
    finally:
        dog.Close()
        print("연결 종료")
