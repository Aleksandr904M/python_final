import torch
import cv2

class ObjectDetection:
    def __init__(self):               # можно указать путь до другой обученной модели
        self.__model = self.__load_model()
        self.classes = self.__model.names   # classes - это словарь
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.__model.to(device)      # перенести модель на устройство

    def __load_model(self):
        model = torch.hub.load('ultralytics/yolov5', 'yolov5x', pretrained=True)
        return model

    def detect_objects(self, image_path):  # путь до картинки
        img = cv2.imread(image_path)       #считать картинку
        if img is None:
            return
        results = self.__model(img)
        detections = results.xyxy[0].cpu().numpy()  # извлекаются координаты, вероятность, и класс

        detected_objects = []
        for detection in detections:
            x1, y1, x2, y2, conf, class_id = detection
            # из словаря classes по id, берется название и вероятность (ограничена 2знаками после запятой)
            label = f"{self.classes[class_id]} {conf:.2f}"
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            # putText() (param: на какую картинку добавляется текст, какой именно текст), верхняя левая координата от
            # которой будет рисоваться текст (- 10 смещен вверх)(для этого уменьшен Y), затем шрифт и его параметры
            cv2.putText(img, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)
            detected_objects.append({
                                    "class": self.classes[class_id],
                                    "confidence": int(conf),
                                    "coordinates": (int(x1), int(y1), int(x2), int(y2))
                                     })

        cv2.imshow("Распознавание", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return img, detected_objects