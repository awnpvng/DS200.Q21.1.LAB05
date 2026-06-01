# PROMPT: XÂY DỰNG HỆ THỐNG ĐẾM NGƯỜI PHÂN TÁN (PYSPARK + YOLO26 NMS-FREE + DYNAMIC CASCADE)

Bạn là một kỹ sư chuyên gia về Hệ thống Dữ liệu lớn (Big Data Engineer) và Thị giác Máy tính (Computer Vision Engineer). Hãy tiến hành viết mã nguồn triển khai chi tiết cho hệ thống "Đếm số lượng người thời gian thực" dựa trên bản đặc tả kỹ thuật dưới đây. 

Hệ thống được chia làm 3 Server độc lập chạy trên kiến trúc Microservices, giao tiếp qua luồng dữ liệu truyền phát kết hợp thuật toán tối ưu Dynamic Cascade và mô hình YOLO26 NMS-Free (Không sử dụng hậu xử lý NMS).

---

## 1. THIẾT KẾ THAM SỐ TẬP TRUNG (config/settings.yaml)

Hãy tạo file cấu hình `config/settings.yaml` với các thông số phân tích động được thiết kế khoa học như sau:

```yaml
system:
  host: "localhost"
  log_level: "INFO"

network_ports:
  server1_gateway: 6100
  server2_processing: 6200
  server3_storage: 6300

model_weights:
  yolo26_path: "models/yolo26_nano.pt"

cascade_parameters:
  # Cấu hình cho tầng Quét Thô (Global Pass)
  global_conf_threshold: 0.25      # Thấp để chấp nhận lọt lưới, không bỏ sót đối tượng nhỏ
  
  # Điều kiện kích hoạt Tầng Quét Tinh (Local Pass - Auto-Crop)
  cascade_trigger_threshold: 0.45  # Nếu độ tin cậy của box dưới mức này -> nghi ngờ và kích hoạt kích hoạt cascade
  density_trigger_limit: 5         # Nếu phát hiện > 5 người trong một cụm khoảng cách sát nhau -> kích hoạt cascade đám đông
  
  # Cấu hình cho tầng Quét Tinh (Local Pass) trên vùng ảnh Crop
  local_conf_threshold: 0.30       # Ngưỡng lọc kết quả cuối cùng sau khi đã zoom cận cảnh
  padding_pixels: 30               # Số pixel mở rộng ra xung quanh vùng crop để tránh mất góc đối tượng

tracking:
  tracker_type: "bytetrack"
  track_buffer_frames: 30          # Số frame giữ lại ID khi đối tượng bị che khuất tạm thời
2. NHIỆM VỤ LẬP TRÌNH CHI TIẾT CHO TỪNG THÀNH PHẦN
Hãy viết mã nguồn Python hoàn chỉnh, xử lý ngoại lệ chặt chẽ (try-except), ghi log rõ ràng cho các file sau đây theo đúng cấu trúc thư mục:

📑 FILE 1: src/utils/networking.py
Viết các hàm helper phục vụ việc truyền tải ảnh qua Socket mạng.

encode_frame_to_base64(frame): Nén khung hình OpenCV (numpy array) thành định dạng JPEG (quality=80) rồi chuyển sang chuỗi Base64 UTF-8.

decode_base64_to_frame(base64_str): Giải mã chuỗi Base64 ngược lại thành numpy array để OpenCV xử lý.

📑 FILE 2: src/server1_gateway/sender.py
Đóng vai trò là Server 1. Kết nối đến Server 2 qua TCP Socket định kỳ theo FPS cấu hình.

Sử dụng OpenCV để đọc luồng video từ file (data/videos/video.mp4) hoặc từ Webcam (0). Nếu không có mã nguồn video, tự động sinh khung hình giả lập (Synthetic Frame).

Đóng gói dữ liệu thành một chuỗi JSON có cấu trúc kết thúc bằng ký tự xuống dòng \n (để Spark Streaming cắt dòng) gồm các trường: type, frame_id (UUID), timestamp, frame_number, data (chuỗi base64).

📑 FILE 3: src/server2_processing/dynamic_cascade.py
Triển khai thuật toán Auto-Zoom thông minh sử dụng YOLO26 NMS-Free.

Hàm run_cascade_pipeline(frame, model):

Global Pass: Chạy mô hình YOLO26 trên toàn bộ frame gốc với conf=global_conf_threshold. Vì YOLO26 là NMS-free nên lấy trực tiếp tọa độ box trả về.

Phân tích: Duyệt qua các box. Nếu có box nào có confidence < cascade_trigger_threshold HOẶC tổng số box trong một vùng cục bộ vượt quá density_trigger_limit, xác định tọa độ bao quanh vùng đó (Bounding Box tổng của cụm).

Local Pass (Auto-Crop): Cắt vùng ảnh đó ra, áp dụng padding_pixels. Tiến hành phóng to vùng ảnh này (Upscale) rồi đưa vào YOLO26 quét lần 2 với conf=local_conf_threshold.

Hợp nhất: Ánh xạ ngược tọa độ các box quét được từ ảnh cắt về tọa độ ảnh gốc. Loại bỏ trùng lặp dựa trên khoảng cách tâm hộp (không dùng NMS gốc của mô hình). Trả về danh sách box cuối cùng.

📑 FILE 4: src/server2_processing/spark_streaming.py
Khởi tạo SparkSession cấu hình chạy local stream.

Sử dụng spark.readStream để lắng nghe dữ liệu từ cổng TCP của Server 1.

Sử dụng cơ chế foreachBatch trên luồng dữ liệu của Spark để đẩy từng Micro-batch frame qua module dynamic_cascade.py và tracker.py nhằm gán track_id (ByteTrack) phân tán.

Sau khi tính toán xong lượng người hiện diện và mã định danh duy nhất (total_unique_persons_counted), đóng gói kết quả JSON và dùng socket đẩy thẳng qua Server 3 (Cổng 6300).

📑 FILE 5: src/server3_storage/receiver_store.py
Đóng vai trò Server 3. Mở một Socket Server lắng nghe dữ liệu JSON trả về từ cụm Spark.

Khi nhận được dữ liệu, tiến hành lưu trữ phi cấu trúc vào thư mục output/results/camera_01_log.json theo dạng append luồng.

In ra màn hình console dashboard thời gian thực: [Thời gian] - Số người hiện tại: X | Tổng số người đã đi qua: Y.

3. YÊU CẦU ĐẦU RA CỦA MÃ NGUỒN
Mã nguồn phải sạch, tuân thủ PEP8, có comment giải thích rõ ràng logic dịch chuyển tọa độ trong Dynamic Cascade.

Các thư viện sử dụng: pyspark, ultralytics (YOLOv12/YOLO26), opencv-python, pyyaml.


#Tree folder
DS200_PersonCounting_BigData/
├── .gitignore                 # Cấu hình bỏ qua các file thừa, video nặng, weights khi push lên Git
├── README.md                  # Hướng dẫn cài đặt, vận hành hệ thống và báo cáo kiến trúc
├── requirements.txt           # Danh sách các thư viện cần cài đặt (pyspark, opencv-python, ultralytics,...)
│
├── config/
│   └── settings.yaml          # File cấu hình tập trung (Ports, Thresholds của Cascade, Path mô hình)
│
├── data/
│   └──                # Thư mục lưu trữ các file video (.mp4) phục vụ việc chạy thử nghiệm
│
├── models/
│   └── yolo26_nano.pt         # File trọng số mô hình YOLO26 cơ chế NMS-Free
│
├── scripts/
│   ├── start_server1.sh       # Bash script khởi chạy nhanh Server 1 (Gateway)
│   ├── start_server2_spark.sh # Bash script submit job lên Spark Cluster (Server 2)
│   └── start_server3.sh       # Bash script khởi chạy nhanh Server 3 (Storage)
│
├── src/
│   ├── __init__.py
│   │
│   ├── server1_gateway/
│   │   ├── __init__.py
│   │   └── sender.py          # SERVER 1: Đọc luồng video/camera, nén frame và stream qua TCP Socket
│   │
│   ├── server2_processing/
│   │   ├── __init__.py
│   │   ├── detector.py        # Bộ điều phối chính kết hợp YOLO26, Cascade và Tracker
│   │   ├── dynamic_cascade.py # Thuật toán Auto-Zoom thông minh (Xử lý Global Pass & Local Pass)
│   │   ├── spark_streaming.py # SERVER 2: Tiếp nhận luồng dữ liệu micro-batch bằng PySpark Streaming
│   │   └── tracker.py         # Triển khai thuật toán ByteTrack để quản lý quỹ đạo và gán Track ID
│   │
│   ├── server3_storage/
│   │   ├── __init__.py
│   │   └── receiver_store.py  # SERVER 3: Socket lắng nghe kết quả từ Spark, ghi file và hiển thị Dashboard
│   │
│   └── utils/
│       ├── __init__.py
│       ├── networking.py      # Các hàm helper mã hóa/giải mã ảnh (Base64) và xử lý luồng byte Socket
│       └── visualization.py   # Công cụ vẽ Bounding Box, Track ID lên frame ảnh phục vụ việc debug/demo
│
└── output/
    └── results/               # Nơi Server 3 tự động xuất các file log kết quả dạng JSON/TXT
        └── camera_01_log.json