## 1. Tạo và sử dụng môi trường ảo (venv)
### Bước 1: Tạo môi trường ảo
Chạy lệnh sau trong Terminal hoặc Command Prompt:

```cmd
python -m venv env
```

- env là tên thư mục chứa môi trường ảo. Bạn có thể thay đổi tên theo ý thích.
Nếu đang dùng Python 3, có thể cần dùng python3 thay vì python.

### Bước 2: Kích hoạt môi trường ảo
- Windows:

```cmd 
env\Scripts\activate
```
macOS/Linux:
```cmd 
source myenv/bin/activate
```

Khi kích hoạt thành công, tên môi trường (vd: (env)) sẽ xuất hiện ở đầu dòng lệnh.
### Bước 3: Cài đặt thư viện trong môi trường ảo
Dùng pip để cài đặt thư viện:

```cmd 
pip install library_name
```
Ví dụ:
```cmd 
pip install requests
```
## 2. Tạo file requirements.txt
### Bước 1: Lưu danh sách các thư viện đã cài đặt
Chạy lệnh sau trong môi trường ảo:
```cmd 
pip freeze > requirements.txt
```
File requirements.txt sẽ chứa danh sách các thư viện và phiên bản tương ứng.

### Bước 2: Cài đặt thư viện từ file requirements.txt
Nếu bạn muốn cài đặt lại thư viện trên một máy khác (hoặc môi trường ảo khác), dùng lệnh:
```cmd
pip install -r requirements.txt
```

- lỗi torch
```cmd
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
```
## 3. Tắt môi trường ảo
Khi hoàn tất công việc, bạn có thể tắt môi trường ảo bằng lệnh:
```cmd
deactivate
```