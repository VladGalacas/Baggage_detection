import cv2
import time
import numpy as np
from logger.logger_config import logger
from utils.utils import counter_decorator
from config import YOLOv7_PATH, SIZE, CLASS_LIST


class RealTimeObjectDetection:

    def __init__(self,
                 model_path=YOLOv7_PATH,
                 class_list=CLASS_LIST,
                 score_threshold=0.6,
                 nms_threshold=0.55,
                 confidence_threshold=0.6,
                 size=SIZE):
        """
        Класс, реализующий обнаружение объектов в реальном времени с помощью библиотеки компьютерного зрения OpenCV
        и предобученной модели нейронной сети формата ONNX. Он содержит несколько методов, которые обрабатывают
        различные аспекты процесса обнаружения объектов.
        :param model_path: Путь, по которому была сохранена модель нейронной сети.
        :param class_list: Список классов, которые должны быть обнаружены.
        :param score_threshold: Порог, используемый для фильтрации боксов.
        :param nms_threshold: Порог, используемый при не максимальном подавлении.
        :param confidence_threshold: Порог, при котором объект считается распознанным.
        :param size: Кортеж с шириной и высотой видео.
        """
        assert isinstance(score_threshold, int | float) and score_threshold >= 0 and score_threshold <= 1, \
            "score_threshold должен иметь тип int или float и его значение должно быть в пределах от 0 до 1"
        assert isinstance(nms_threshold, int | float) and nms_threshold >= 0 and nms_threshold <= 1, \
            "nms_threshold должен иметь тип int или float и его значение должно быть в пределах от 0 до 1"
        assert isinstance(confidence_threshold,
                          int | float) and confidence_threshold >= 0 and confidence_threshold <= 1, \
            "confidence_threshold должен иметь тип int или float и его значение должно быть в пределах от 0 до 1"
        assert isinstance(class_list, list | tuple), "class_list должен иметь тип list или tuple"
        assert isinstance(model_path, str), "model_path должен иметь тип str"
        assert isinstance(size, list | tuple), "Размеры должны иметь тип list или tuple"
        assert len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int), \
            "Список/кортёж size должен иметь 2 элемента, и эти элементы должны иметь тип int"

        self.MODEL_PATH = model_path
        self.SCORE_THRESHOLD = score_threshold
        self.NMS_THRESHOLD = nms_threshold
        self.CONFIDENCE_THRESHOLD = confidence_threshold
        self.CLASS_LIST = class_list
        self.SIZE = size

        self.colors = np.random.uniform(0, 255, size=(len(self.CLASS_LIST), 3))

    def init_model(self):
        net, output_layers = self._build_model()
        capture = self.load_capture()
        return net, output_layers, capture

    def _build_model(self):
        try:
            net = cv2.dnn.readNet(self.MODEL_PATH)
            layer_names = net.getLayerNames()
            output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
            is_cuda = cv2.cuda.getCudaEnabledDeviceCount()
            if is_cuda:
                logger.info('Использование CUDA')
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
            else:
                logger.info('Использование CPU')
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            return net, output_layers

        except Exception as exc:
            logger.error(f'Возникла ошибка {exc}')

    def _detect(self, image, net, output_layers):
        assert isinstance(image, np.ndarray), "Переменная image должна иметь тип numpy.ndarray"
        assert isinstance(net, cv2.dnn.Net), "Переменная net должна иметь тип cv2.dnn.Net"
        assert isinstance(output_layers, list), "Переменная output_layers должна иметь тип list"

        try:
            blob = cv2.dnn.blobFromImage(image, 1 / 255.0, self.SIZE, swapRB=True, crop=False)
            net.setInput(blob)
            preds = net.forward(output_layers)
            return preds
        except Exception as exc:
            logger.error(f'Возникла ошибка {exc}')

    def load_capture(self):
        capture = cv2.VideoCapture(0)
        if not capture.isOpened():
            logger.error("Невозможно открыть веб-камеру")
            raise IOError('Невозможно открыть веб-камеру')
        else:
            logger.info('Успешное открытие веб-камеры')
            return capture

    def _wrap_detection(self, input_image, output_data):
        assert isinstance(input_image, np.ndarray), "Переменная input_image должна иметь тип numpy.ndarray"
        assert isinstance(output_data, np.ndarray), "Переменная output_data должна иметь тип numpy.ndarray"

        class_ids = []
        confidences = []
        boxes = []
        rows = output_data.shape[1]
        image_width, image_height, _ = input_image.shape
        x_factor = image_width / self.SIZE[0]
        y_factor = image_height / self.SIZE[1]
        try:
            for r in range(rows):
                row = output_data[0, r]
                confidence = row[4]
                if confidence >= self.CONFIDENCE_THRESHOLD:
                    classes_scores = row[5:]
                    class_id = np.argmax(classes_scores)
                    confidences.append(confidence)

                    class_ids.append(class_id)
                    x, y, w, h = row[0].tolist(), row[1].tolist(), row[2].tolist(), row[3].tolist()
                    left = int((x - 0.5 * w) * x_factor)
                    top = int((y - 0.5 * h) * y_factor)
                    width = int(w * x_factor)
                    height = int(h * y_factor)
                    box = np.array([left, top, width, height])
                    boxes.append(box)
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, self.SCORE_THRESHOLD, self.NMS_THRESHOLD)
            result_class_ids = []
            result_confidences = []
            result_boxes = []
            for i in indexes:
                result_confidences.append(confidences[i])
                result_class_ids.append(class_ids[i])
                result_boxes.append(boxes[i])

            # logger.info('Successful wrap')
            return result_class_ids, result_confidences, result_boxes

        except Exception as exc:
            logger.error(f"Невозможно применить модель к кадру! Возникла ошибка {exc}")

    def _format_yolo(self, image, COLOUR=[0, 0, 0]):
        assert isinstance(image, np.ndarray), "Переменная image должна иметь тип numpy.ndarray"
        assert isinstance(COLOUR, list | tuple), "Переменная COLOUR должна иметь тип list или tuple"

        h, w, layers = image.shape
        if h > self.SIZE[1]:
            ratio = self.SIZE[1] / h
            image = cv2.resize(image, (int(image.shape[1] * ratio), int(image.shape[0] * ratio)))
        h, w, layers = image.shape
        if w > self.SIZE[0]:
            ratio = self.SIZE[0] / w
            image = cv2.resize(image, (int(image.shape[1] * ratio), int(image.shape[0] * ratio)))
        h, w, layers = image.shape
        if h < self.SIZE[1] and w < self.SIZE[0]:
            hless = self.SIZE[1] / h
            wless = self.SIZE[0] / w
            if (hless < wless):
                image = cv2.resize(image, (int(image.shape[1] * hless), int(image.shape[0] * hless)))
            else:
                image = cv2.resize(image, (int(image.shape[1] * wless), int(image.shape[0] * wless)))
        h, w, layers = image.shape
        if h < self.SIZE[1]:
            df = self.SIZE[1] - h
            df /= 2
            image = cv2.copyMakeBorder(image, int(df), int(df), 0, 0, cv2.BORDER_CONSTANT, value=COLOUR)
        if w < self.SIZE[0]:
            df = self.SIZE[0] - w
            df /= 2
            image = cv2.copyMakeBorder(image, 0, 0, int(df), int(df), cv2.BORDER_CONSTANT, value=COLOUR)
        image = cv2.resize(image, self.SIZE, interpolation=cv2.INTER_AREA)

        return image

    # ---------------------------------------------------------------------
    @counter_decorator
    def get_frame(self, capture, starting_time):
        assert isinstance(capture, cv2.VideoCapture), "Переменная capture должна иметь тип cv2.VideoCapture"
        assert isinstance(starting_time, float), "Переменная starting_time должна иметь тип float"

        if capture.isOpened():
            ret, img = capture.read()
            if ret:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = self._format_yolo(img)
                return img
            logger.error('Возникла ошибка при чтении кадра')
            return None
        else:
            logger.warning('Поток закрыт')
            return None

    def get_detected_frame(self, net, output_layers, frame):
        assert isinstance(net, cv2.dnn.Net), "Переменная net должна иметь тип cv2.dnn.Net"
        assert isinstance(output_layers, list), "Переменная output_layers должна иметь тип list"

        img = self._format_yolo(frame)
        outs = self._detect(img, net, output_layers)
        class_ids, confidences, boxes = self._wrap_detection(img, outs[0])
        meta = list(zip(class_ids, confidences, boxes))

        for (classid, confidence, box) in meta:
            color = self.colors[int(classid) % len(self.colors)]
            cv2.rectangle(img, box, color, 2)
            cv2.rectangle(img, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
            cv2.putText(img, f'{self.CLASS_LIST[classid]}:{str(round(confidence, 2))}',
                        (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0))

        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        logger.info('Успешное применение модели к кадру')
        return img, meta



class ImageObjectDetection(RealTimeObjectDetection):

    def __init__(self,
                 model_path=YOLOv7_PATH,
                 class_list=CLASS_LIST,
                 score_threshold=0.6,
                 nms_threshold=0.55,
                 confidence_threshold=0.6,
                 size=SIZE):
        """
        Класс, реализующий обнаружение объектов на изображении с помощью библиотеки компьютерного зрения OpenCV
        и предобученной модели нейронной сети формата ONNX. Он содержит несколько методов, которые обрабатывают
        различные аспекты процесса обнаружения объектов.
        :param model_path: Путь, по которому была сохранена модель нейронной сети.
        :param class_list: Список классов, которые должны быть обнаружены.
        :param score_threshold: Порог, используемый для фильтрации боксов.
        :param nms_threshold: Порог, используемый при не максимальном подавлении.
        :param confidence_threshold: Порог, при котором объект считается распознанным.
        :param size: Кортеж с шириной и высотой изображения.
        """
        super().__init__(model_path, class_list, score_threshold, nms_threshold, confidence_threshold, size)

    def init_model(self):
        net, output_layers = self._build_model()
        return net, output_layers

    def load_capture(self, image_path):
        assert isinstance(image_path, str), "Переменная image_path должена иметь тип str"

        try:
            capture = cv2.imread(image_path)
            logger.info(f'Успешное октрытие изображения {image_path}')
            return capture
        except Exception as exc:
            logger.error(f'Ошибка при открытии изображения {image_path}. Возникла ошибка {exc}')
            raise IOError(f'Невозможно открыть изображения {image_path}')

    def get_detected_frame(self, capture, net, output_layers):
        assert isinstance(capture, np.ndarray), "Переменная capture должна иметь тип numpy.ndarray"
        assert isinstance(net, cv2.dnn.Net), "Переменная net должна иметь тип cv2.dnn.Net"
        assert isinstance(output_layers, list), "Переменная output_layers должна иметь тип list"

        try:
            img = self._format_yolo(capture)
            outs = self._detect(img, net, output_layers)
            class_ids, confidences, boxes = self._wrap_detection(img, outs[0])
            meta = list(zip(class_ids, confidences, boxes))
            for (classid, confidence, box) in zip(class_ids, confidences, boxes):
                color = self.colors[int(classid) % len(self.colors)]
                cv2.rectangle(img, box, color, 2)
                cv2.rectangle(img, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
                cv2.putText(img, f'{self.CLASS_LIST[classid]}:{str(round(confidence, 2))}', (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            logger.info("Успешное применение модели к изображению")
            return img, meta
        except Exception as exc:
            logger.error(f'Неудачная попытка применить модель к изображению. Произошла ошибка {exc}')


class VideoObjectDetection(RealTimeObjectDetection):

    def __init__(self,
                 model_path=YOLOv7_PATH,
                 class_list=CLASS_LIST,
                 score_threshold=0.6,
                 nms_threshold=0.55,
                 confidence_threshold=0.6,
                 size=SIZE):
        """
        Класс, реализующий обнаружение объектов на видео с помощью библиотеки компьютерного зрения OpenCV
        и предобученной модели нейронной сети формата ONNX. Он содержит несколько методов, которые обрабатывают
        различные аспекты процесса обнаружения объектов.
        :param model_path: Путь, по которому была сохранена модель нейронной сети.
        :param class_list: Список классов, которые должны быть обнаружены.
        :param score_threshold: Порог, используемый для фильтрации боксов.
        :param nms_threshold: Порог, используемый при не максимальном подавлении.
        :param confidence_threshold: Порог, при котором объект считается распознанным.
        :param size: Кортеж с шириной и высотой видео.
        """
        super().__init__(model_path, class_list, score_threshold, nms_threshold, confidence_threshold, size)

    def init_model(self):
        net, output_layers = self._build_model()
        return net, output_layers

    def load_capture(self, video_path):
        assert isinstance(video_path, str), "Переменная video_path должна иметь тип str"

        try:
            capture = cv2.VideoCapture(video_path)

            if not capture.isOpened():
                logger.error(f'Поток видео {video_path} закрыт')
                raise IOError(f'Невозможно открыть видео {video_path}')
            else:
                logger.info(f'Успешное открытие видео {video_path}')
                return capture
        except Exception as exc:
            logger.error(f'cv2 не может открыть видео {video_path}. Произошла ошибка {exc}')
