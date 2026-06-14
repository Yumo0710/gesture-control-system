import cv2

from control.virtual_mouse import VirtualMouse
from vision.hand_detector import HandDetector
from vision.webcam import Webcam


def main():
    webcam = Webcam()
    detector = HandDetector(require_mediapipe=True)
    cursor = VirtualMouse(smoothing=0.3)

    print("Virtual Mouse 測試啟動，按 Q 或 Esc 結束。")

    while True:
        frame = webcam.get_frame()
        if frame is None:
            break

        frame, hand_landmarks = detector.detect_hands(frame)

        if hand_landmarks:
            # 獨立測試使用食指指尖控制游標絕對位置。
            index_tip = hand_landmarks.landmark[8]
            screen_x, screen_y = cursor.move(index_tip.x, index_tip.y)

            frame_height, frame_width = frame.shape[:2]
            overlay_x = int(index_tip.x * frame_width)
            overlay_y = int(index_tip.y * frame_height)

            cv2.circle(frame, (overlay_x, overlay_y), 12, (0, 255, 0), cv2.FILLED)
            cv2.putText(
                frame,
                f"Cursor: {screen_x}, {screen_y}",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        cv2.imshow("Virtual Mouse Control", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
