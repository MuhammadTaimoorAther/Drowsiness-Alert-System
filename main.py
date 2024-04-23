import cv2
import os
from keras.models import load_model
import numpy as np
from pygame import mixer
import time
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder


KV = '''
MDScreen:
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'top'
        MDTopAppBar:
            title: "Drowsiness Alert System"
            specific_text_color: app.theme_cls.accent_color 
    Image:
        size_hint_y:1
        size_hint_x:1
        pos_hint:{'center_x':0.5, 'center_y':0.6}
        source: 'img.png'
    MDRectangleFlatButton:
        text: "START DETECTION"
        pos_hint: {'center_x': 0.5, 'center_y': 0.2}
        on_release: app.play()
    
'''

class MainApp(MDApp):
    def __init__(self):
        super().__init__()
        self.kvs = Builder.load_string(KV)

    def build(self):
        screen = Screen()
        screen.add_widget(self.kvs)
        return screen
    def play(self):


        def load_cascades_and_model():
            face_cascade = cv2.CascadeClassifier('haar cascade files\haarcascade_frontalface_alt.xml')
            leye_cascade = cv2.CascadeClassifier('haar cascade files\haarcascade_lefteye_2splits.xml')
            reye_cascade = cv2.CascadeClassifier('haar cascade files\haarcascade_righteye_2splits.xml')

            trained_model = load_model('models/cnncat2.h5')

            return face_cascade, leye_cascade, reye_cascade, trained_model

        def detect_eyes(frame, face_cascade, leye_cascade, reye_cascade, model):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray, minNeighbors=5, scaleFactor=1.1, minSize=(25, 25))
            left_eye = leye_cascade.detectMultiScale(gray)
            right_eye = reye_cascade.detectMultiScale(gray)

            return faces, left_eye, right_eye

        def main():
            mixer.init()
            sound = mixer.Sound('alarm.wav')
            alarm_active = False  # Variable to track if the alarm is currently active

            face_cascade, leye_cascade, reye_cascade, model = load_cascades_and_model()

            cap = cv2.VideoCapture(0)
            font = cv2.FONT_HERSHEY_COMPLEX_SMALL
            count = 0
            score = 0
            thicc = 2

            while True:
                ret, frame = cap.read()
                height, width = frame.shape[:2]

                faces, left_eye, right_eye = detect_eyes(frame, face_cascade, leye_cascade, reye_cascade, model)

                cv2.rectangle(frame, (0, height - 50), (200, height), (0, 0, 0), thickness=cv2.FILLED)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 100, 100), 1)

                # Initialize lpred outside the for loop
                lpred = None

                for (x, y, w, h) in left_eye:
                    l_eye = frame[y:y + h, x:x + w]
                    count += 1
                    l_eye = cv2.cvtColor(l_eye, cv2.COLOR_BGR2GRAY)
                    l_eye = cv2.resize(l_eye, (24, 24))
                    l_eye = l_eye / 255
                    l_eye = l_eye.reshape(24, 24, -1)
                    l_eye = np.expand_dims(l_eye, axis=0)
                    lpred = np.argmax(model.predict(l_eye), axis=-1)
                    break

                for (x, y, w, h) in right_eye:
                    r_eye = frame[y:y + h, x:x + w]
                    count += 1
                    r_eye = cv2.cvtColor(r_eye, cv2.COLOR_BGR2GRAY)
                    r_eye = cv2.resize(r_eye, (24, 24))
                    r_eye = r_eye / 255
                    r_eye = r_eye.reshape(24, 24, -1)
                    r_eye = np.expand_dims(r_eye, axis=0)
                    rpred = np.argmax(model.predict(r_eye), axis=-1)
                    break

                if lpred is not None:
                    if rpred[0] == 0 and lpred[0] == 0:
                        score += 1
                        cv2.putText(frame, "Closed", (10, height - 20), font, 1, (255, 255, 255), 1, cv2.LINE_AA)
                    else:
                        score -= 1
                        cv2.putText(frame, "Open", (10, height - 20), font, 1, (255, 255, 255), 1, cv2.LINE_AA)

                if score < 0:
                    score = 0

                cv2.putText(frame, 'Score:' + str(score), (100, height - 20), font, 1, (255, 255, 255), 1, cv2.LINE_AA)

                if score > 15 and not alarm_active:
                    cv2.imwrite(os.path.join(os.getcwd(), 'image.jpg'), frame)
                    try:
                        sound.play()
                        alarm_active = True
                    except Exception as e:
                        print(f"Error playing sound: {e}")

                    if thicc < 16:
                        thicc = thicc + 2
                    else:
                        thicc = thicc - 2
                        if thicc < 2:
                            thicc = 2

                    cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), thicc)
                elif score <= 15 and alarm_active:
                    sound.stop()
                    alarm_active = False

                cv2.imshow('frame', frame)

                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
                elif key & 0xFF == ord('s') and alarm_active:  # Press 's' to stop the alarm manually
                    sound.stop()
                    alarm_active = False

            cap.release()
            cv2.destroyAllWindows()

        if __name__ == "__main__":
            main()


ma = MainApp()
ma.run()
